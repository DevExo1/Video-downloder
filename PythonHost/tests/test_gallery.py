"""Real gallery-dl transfers over local HTTP, without contacting a third-party site."""
import concurrent.futures
import contextlib
import os
import re
import time
import unittest
from unittest import mock

from tests import support
from ytdlpgui_host import gallery

APP = support.install_fake_app()

try:
    from gallery_dl import config, extractor
    from gallery_dl.extractor.common import Extractor, Message
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def setUpModule():
    support.configure_engine()


@unittest.skipUnless(AVAILABLE, 'Fetch iOS dependencies to test gallery-dl')
class GalleryTests(unittest.TestCase):
    def setUp(self):
        self.destination = support.output_dir()
        self.server = support.LocalServer({
            '/one.jpg': (b'first image', 'image/jpeg'),
            '/two.jpg': (b'second image', 'image/jpeg'),
            '/slow.jpg': (b'x' * 1024 * 1024, 'image/jpeg', 0.025),
        }).__enter__()
        self.addCleanup(self.server.__exit__, None, None, None)
        server = self.server

        class GalleryExtractor(Extractor):
            category = 'testgallery'
            subcategory = 'album'
            directory_fmt = ('{category}', 'album')
            filename_fmt = '{id}.{extension}'
            archive_fmt = '{id}'

            def __init__(self, url):
                super().__init__(re.match(r".*", url))
                self.url = url

            def items(self):
                yield Message.Directory, '', {'title': 'Local gallery'}
                names = ('slow',) if self.url.endswith('/slow') else ('one', 'two')
                for name in names:
                    yield Message.Url, server.url('/' + name + '.jpg'), {'id': name, 'extension': 'jpg'}

        self.patch = mock.patch.object(extractor, 'find', side_effect=GalleryExtractor)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def download(self, *arguments, path='/album', job_id=None, destination=None):
        job_id = job_id or support.new_job_id()
        argv = [gallery.MARKER, '--ignore-config', '--no-input', '--no-colors', '--no-mtime',
                '--destination', destination or self.destination, *arguments, '--', self.server.url(path)]
        return job_id, support.call('download', {'job_id': job_id, 'argv': argv})

    def test_multiple_files_and_events(self):
        job_id, result = self.download('--write-info-json')
        self.assertEqual(result.get('exit_code'), 0, result)
        self.assertEqual(len(result['files']), 2, APP.log(job_id))
        self.assertEqual([support.read(path) for path in result['files']], [b'first image', b'second image'])
        self.assertTrue(all('/testgallery/album/' in path for path in result['files']))
        self.assertEqual(len(APP.events(job_id, 'file')), 2)
        self.assertTrue(os.path.isfile(os.path.join(self.destination, 'testgallery', 'album', 'info.json')))
        self.assertTrue(APP.events(job_id, 'progress'))

    def test_filename_and_range(self):
        _, result = self.download('--filename', 'custom-{id}.{extension}', '--range', '2')
        self.assertEqual(result.get('exit_code'), 0, result)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(os.path.basename(result['files'][0]), 'custom-two.jpg')

    def test_archive_and_existing_files(self):
        archive = os.path.join(self.destination, 'archive.sqlite3')
        _, first = self.download('--download-archive', archive)
        self.assertEqual(first.get('exit_code'), 0, first)
        self.assertTrue(os.path.isfile(archive))
        _, second = self.download('--download-archive', archive)
        self.assertEqual(second.get('exit_code'), 0, second)
        self.assertEqual(second['files'], first['files'])
        # An archived file removed from disk must not become a phantom output in history.
        os.remove(first['files'][0])
        _, third = self.download('--download-archive', archive)
        self.assertEqual(len(third['files']), 1)

    def test_cancellation_during_transfer(self):
        job_id = support.new_job_id()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            task = pool.submit(self.download, path='/slow', job_id=job_id)
            deadline = time.monotonic() + 10
            while not APP.events(job_id, 'progress') and not task.done() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(APP.events(job_id, 'progress'))
            support.call('cancel', {'job_id': job_id})
            _, result = task.result(timeout=10)
        self.assertTrue(result.get('cancelled'), result)
        self.assertEqual(result['exit_code'], 101)
        self.assertEqual(result['files'], [])

    def test_waiting_cancellation_and_configuration_isolation(self):
        job_id = support.new_job_id()
        with gallery._lock, concurrent.futures.ThreadPoolExecutor() as pool:
            task = pool.submit(self.download, job_id=job_id)
            time.sleep(0.1)
            support.call('cancel', {'job_id': job_id})
            _, result = task.result(timeout=5)
        self.assertTrue(result.get('cancelled'), result)
        before = dict(config._config)
        second = support.output_dir()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            tasks = [pool.submit(self.download, destination=folder) for folder in [self.destination, second]]
            results = [task.result(timeout=10)[1] for task in tasks]
        self.assertTrue(all(r['exit_code'] == 0 for r in results), results)
        self.assertTrue(all(p.startswith(self.destination) for p in results[0]['files']))
        self.assertTrue(all(p.startswith(second) for p in results[1]['files']))
        self.assertEqual(config._config, before)

    def test_unsafe_arguments_are_rejected(self):
        for arguments in [('--exec', 'touch /tmp/unwanted'), ('--option', 'postprocessors=x'),
                          ('--filter', '__import__("os")'), ('--config', '/tmp/config'),
                          ('--filename', '\\fE__import__("os")')]:
            with self.subTest(arguments=arguments):
                _, result = self.download(*arguments)
                self.assertFalse(result['ok'], result)

    def test_cli_print_markers_name_every_real_file(self):
        # Exercise the very same CLI options used by the Mac, with the real gallery-dl main.
        import io
        import sys
        import gallery_dl
        import json
        out = io.StringIO()
        argv = ['gallery-dl', '--ignore-config', '--no-input', '--no-colors',
                '--destination', self.destination,
                '--Print', 'after:__YTDLPGUI_GALLERY_FILE__{_path!j}',
                '--Print', 'skip:__YTDLPGUI_GALLERY_FILE__{_path!j}',
                '--', self.server.url('/album')]
        before = dict(config._config)
        try:
            with mock.patch.object(sys, 'argv', argv), contextlib.redirect_stdout(out):
                try:
                    gallery_dl.main()
                except SystemExit as error:
                    self.assertEqual(error.code or 0, 0)
            paths = [json.loads(line.removeprefix('__YTDLPGUI_GALLERY_FILE__'))
                     for line in out.getvalue().splitlines() if line.startswith('__YTDLPGUI_GALLERY_FILE__')]
            self.assertEqual(len(paths), 2, out.getvalue())
            self.assertTrue(all(os.path.isfile(path) for path in paths), paths)
        finally:
            config._config.clear()
            config._config.update(before)

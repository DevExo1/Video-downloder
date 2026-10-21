"""gallery-dl adapter for the embedded engine.

The CLI entry point mutates global state and installs process hooks. Instead we run
DownloadJob with a bounded set of app-generated options. Gallery jobs are serialized
because gallery-dl's configuration is global; yt-dlp jobs can still run concurrently.
"""

import logging
import os
import threading

from . import engine, jobs
from .errors import HostError

MARKER = '--ytdlpgui-gallery-dl'
_lock = threading.Lock()
_SWITCHES = {'--ignore-config', '--no-input', '--no-colors', '--no-mtime',
             '--write-info-json', '--no-skip'}
_VALUES = {'--destination', '--filename', '--range', '--cookies', '--proxy',
           '--user-agent', '--limit-rate', '--download-archive', '--restrict-filenames'}


def _parse(argv):
    if not isinstance(argv, list) or not all(isinstance(arg, str) for arg in argv):
        raise HostError('Invalid gallery-dl arguments.')
    index = 0
    while index < len(argv):
        flag = argv[index]
        if flag == '--':
            if len(argv[index + 1:]) != 1 or not argv[-1].startswith(('https://', 'http://')):
                raise HostError('Give exactly one web link to gallery-dl.')
            break
        if flag in _SWITCHES:
            index += 1
        elif flag in _VALUES and index + 1 < len(argv):
            index += 2
        else:
            raise HostError(f'Unsupported embedded gallery-dl option: {flag}')
    else:
        raise HostError('There is no gallery link to download.')

    from gallery_dl import option

    parser = option.build_parser()

    def invalid(message):
        raise HostError(f'Invalid gallery-dl options: {message}')

    parser.error = invalid
    parsed = parser.parse_args(argv)
    if parsed.filename and parsed.filename.startswith(('\\f', '\f')):
        raise HostError('Python expressions are not supported in gallery filenames.')
    return parsed


def download(payload):
    job_id = payload.get('job_id')
    if not isinstance(job_id, str) or not job_id:
        raise HostError('The engine was asked to start a gallery job without an ID.')
    try:
        from gallery_dl import config, job as gallery_job, output
    except ImportError as error:
        raise HostError('gallery-dl is missing from this build. Fetch the iOS dependencies and rebuild.') from error
    args = _parse(payload['argv'][1:])

    with jobs.registered(job_id) as job:
        logger = jobs.JobLogger(job)
        acquired = False
        try:
            # Register before waiting so cancellation also works for a waiting gallery.
            while not acquired:
                job.check_cancelled()
                acquired = _lock.acquire(timeout=0.1)
            job.check_cancelled()
            return _run(job, args, logger, config, gallery_job, output)
        except jobs.JobCancelled:
            return {'ok': True, 'exit_code': 101, 'cancelled': True, 'files': list(job.files)}
        except Exception as error:
            if job.cancel_requested:
                return {'ok': True, 'exit_code': 101, 'cancelled': True, 'files': list(job.files)}
            logger.error(f'ERROR: {str(error) or type(error).__name__}')
            return {'ok': True, 'exit_code': 1, 'cancelled': False, 'files': list(job.files)}
        finally:
            if acquired:
                _lock.release()


def _run(job, args, logger, config, gallery_job, output):
    class Reporter(output.NullOutput):
        def start(self, path):
            job.check_cancelled()
            logger.info(f'[download] Destination: {path}')
            job.report_progress({'status': 'downloading', 'downloaded_bytes': 0, 'filename': path})

        def progress(self, bytes_total, bytes_downloaded, bytes_per_second):
            job.report_progress({'status': 'downloading', 'total_bytes': bytes_total,
                                 'downloaded_bytes': bytes_downloaded, 'speed': bytes_per_second})

        def success(self, path):
            job.check_cancelled()
            path = os.path.abspath(path)
            if os.path.isfile(path) and path not in job.files:
                job.files.append(path)
                job.emit({'type': 'file', 'path': path, 'main': True})
                logger.info(f'[gallery-dl] Saved {os.path.basename(path)}')

        skip = success

    class DownloadJob(gallery_job.DownloadJob):
        def __init__(self, url, parent=None):
            super().__init__(url, parent)
            self.out = Reporter()

        def handle_url(self, url, kwdict):
            job.check_cancelled()
            return super().handle_url(url, kwdict)

        def handle_queue(self, url, kwdict):
            job.check_cancelled()
            return super().handle_queue(url, kwdict)

    owner_thread = threading.get_ident()

    class LogHandler(logging.Handler):
        def emit(self, record):
            if record.thread != owner_thread:
                return
            message = record.getMessage()
            if record.levelno >= logging.ERROR:
                logger.error('ERROR: ' + message)
            elif record.levelno >= logging.WARNING:
                logger.warning(message)

    original = dict(config._config)
    handler = LogHandler()
    root_logger = logging.getLogger()
    config._config.clear()
    root_logger.addHandler(handler)
    try:
        # No external programs, arbitrary postprocessors, config files or Python expressions.
        config.set((), 'input', False)
        config.set((), 'async', False)
        config.set((), 'cookies-update', False)
        config.set(('output',), 'mode', 'null')
        config.set(('downloader', 'ytdl'), 'enabled', False)
        config.set(('downloader', 'ytdlp'), 'enabled', False)
        config.set(('downloader', 'http'), 'mtime', False)
        cache_dir = engine.settings().cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            config.set(('cache',), 'file', os.path.join(cache_dir, 'gallery-dl-cache.sqlite3'))
        for path, key, value in args.options:
            config.set(path, key, value)
        if args.filename:
            config.set((), 'filename', '{filename}.{extension}' if args.filename == '/O' else args.filename)
        if args.postprocessors:
            config.set((), 'postprocessors', args.postprocessors)
        gallery_job.FLAGS.clear()

        def work():
            downloader = DownloadJob(args.urls[0])
            downloader.run()
            return downloader.status

        status = job.run(work)
        job.check_cancelled()
        return {'ok': True, 'exit_code': int(status or 0), 'cancelled': False, 'files': list(job.files)}
    finally:
        config._config.clear()
        config._config.update(original)
        gallery_job.FLAGS.clear()
        root_logger.removeHandler(handler)

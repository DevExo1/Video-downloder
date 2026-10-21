import Foundation
import Testing

@testable import YTDLPGUI

@Suite("gallery-dl integration")
struct GalleryDLTests {
    @Test("Older options keep yt-dlp as their backend")
    func legacyOptions() throws {
        let options = try JSONDecoder().decode(DownloadOptions.self, from: Data(#"{"kind":"audio"}"#.utf8))
        #expect(options.backend == .ytdlp)
        #expect(options.kind == .audio)
        #expect(options.galleryFilename.isEmpty)
        #expect(options.galleryRange.isEmpty)
    }

    @Test("Gallery options survive history persistence and retain their backend")
    func history() throws {
        var options = DownloadOptions()
        options.backend = .galleryDL
        options.galleryFilename = "{id}.{extension}"
        options.galleryRange = "1-20"
        let entry = HistoryEntry(title: "Gallery", sourceURL: "https://example.com/gallery", formatSummary: options.formatSummary,
                                 kind: options.kind, succeeded: true, options: options)
        let restored = try JSONDecoder().decode(HistoryEntry.self, from: JSONEncoder().encode(entry))
        #expect(restored.options == options)
        #expect(restored.formatSummary == "Gallery · Original files")
    }

    @Test("Gallery CLI options cannot inherit yt-dlp arguments or templates")
    func separateArguments() {
        var options = DownloadOptions()
        options.backend = .galleryDL
        options.outputDirectory = URL(fileURLWithPath: "/tmp/Gallery Downloads")
        options.customArguments = "--exec touch --output wrong --format bestaudio"
        options.outputTemplate = "%(title)s.%(ext)s"
        options.galleryFilename = "{id}.{extension}"
        options.galleryRange = "2-5"
        options.useDownloadArchive = true
        options.downloadArchivePath = "/tmp/archive.txt"
        options.cookieBrowser = .firefox
        let args = GalleryDLArguments.download(url: "https://example.com/gallery?a=1&b=2", options: options)
        #expect(args.suffix(2) == ["--", "https://example.com/gallery?a=1&b=2"])
        #expect(args.contains("/tmp/Gallery Downloads"))
        #expect(args.contains("{id}.{extension}"))
        #expect(args.contains("/tmp/archive.txt.gallery-dl.sqlite3"))
        #expect(args.contains("firefox"))
        #expect(!args.contains("--exec"))
        #expect(!args.contains("--format"))
        #expect(!args.contains(options.outputTemplate))
        #expect(args.contains("after:" + GalleryDLArguments.fileMarker + "{_path!j}"))
    }

    @Test("Embedded routing keeps browser access and CLI print hooks out of the host")
    func embeddedRouting() {
        var options = DownloadOptions()
        options.backend = .galleryDL
        options.cookieBrowser = .chrome
        options.cookieFilePath = "/tmp/cookies.txt"
        let argv = ArgumentBuilder.embeddedDownloadArguments(url: "https://example.com/gallery", options: options,
                                                            capabilities: EmbeddedEngineCapabilities())
        #expect(argv.first == GalleryDLArguments.embeddedMarker)
        #expect(argv.contains("--cookies"))
        #expect(!argv.contains("--cookies-from-browser"))
        #expect(!argv.contains("--Print"))
    }

    @Test("File markers decode escaped paths and reject missing files")
    func fileReporting() throws {
        let directory = FileManager.default.temporaryDirectory.appending(path: UUID().uuidString)
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: directory) }
        let file = directory.appending(path: "image \"one\"\n.jpg")
        try Data([1, 2, 3]).write(to: file)
        let encoded = String(decoding: try JSONEncoder().encode(file.path(percentEncoded: false)), as: UTF8.self)
        #expect(GalleryDLArguments.fileURL(from: GalleryDLArguments.fileMarker + encoded, outputDirectory: directory) == file)
        #expect(GalleryDLArguments.fileURL(from: GalleryDLArguments.fileMarker + "\"missing.jpg\"", outputDirectory: directory) == nil)
        #expect(GalleryDLArguments.fileURL(from: "plain output", outputDirectory: directory) == nil)
    }
}

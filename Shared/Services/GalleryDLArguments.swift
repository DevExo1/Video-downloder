import Foundation

/// gallery-dl has its own option syntax. Never forward yt-dlp custom arguments to it.
enum GalleryDLArguments {
    static let embeddedMarker = "--ytdlpgui-gallery-dl"
    static let fileMarker = "__YTDLPGUI_GALLERY_FILE__"

    static func validationMessage(for options: DownloadOptions) -> String? {
        let filename = options.galleryFilename.trimmingCharacters(in: CharacterSet(charactersIn: " \t\r\n"))
        if filename.hasPrefix("\\f") || filename.hasPrefix("\u{000C}") {
            return "Use a gallery filename template with {keywords}; Python expressions are not supported."
        }
        if options.useDownloadArchive, options.downloadArchivePath.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty {
            #if os(macOS)
            return "Choose an archive base path, or turn the gallery archive off."
            #endif
        }
        return nil
    }

    static func download(url: String, options: DownloadOptions, embedded: Bool = false) -> [String] {
        var args = ["--ignore-config", "--no-input", "--no-colors", "--no-mtime",
                    "--destination", options.outputDirectory.path(percentEncoded: false)]
        let filename = options.galleryFilename.trimmingCharacters(in: CharacterSet(charactersIn: " \t\r\n"))
        if !filename.isEmpty, !filename.hasPrefix("\\f"), !filename.hasPrefix("\u{000C}") {
            args += ["--filename", filename]
        }
        let range = options.galleryRange.trimmingCharacters(in: .whitespacesAndNewlines)
        if !range.isEmpty { args += ["--range", range] }
        if !options.cookieFilePath.isEmpty { args += ["--cookies", options.cookieFilePath] }
        if !embedded, let browser = options.cookieBrowser.ytdlpValue {
            args += ["--cookies-from-browser", browser]
        }
        if !options.proxy.isEmpty { args += ["--proxy", options.proxy] }
        if !options.userAgent.isEmpty { args += ["--user-agent", options.userAgent] }
        if !options.rateLimit.isEmpty { args += ["--limit-rate", options.rateLimit] }
        if options.useDownloadArchive, !options.downloadArchivePath.isEmpty {
            // gallery-dl uses SQLite, whereas yt-dlp uses a text archive.
            args += ["--download-archive", options.downloadArchivePath + ".gallery-dl.sqlite3"]
        }
        if options.writeInfoJSON { args.append("--write-info-json") }
        if options.restrictFilenames { args += ["--restrict-filenames", "ascii"] }
        if options.overwriteExisting { args.append("--no-skip") }
        if !embedded {
            args += ["--Print", "after:" + fileMarker + "{_path!j}",
                     "--Print", "skip:" + fileMarker + "{_path!j}"]
        }
        return args + ["--", url]
    }

    static func fileURL(from line: String, outputDirectory: URL) -> URL? {
        guard line.hasPrefix(fileMarker),
              let data = String(line.dropFirst(fileMarker.count)).data(using: .utf8),
              let path = try? JSONDecoder().decode(String.self, from: data) else { return nil }
        let url = path.hasPrefix("/") ? URL(fileURLWithPath: path) : outputDirectory.appending(path: path)
        return FileManager.default.fileExists(atPath: url.path(percentEncoded: false)) ? url : nil
    }
}

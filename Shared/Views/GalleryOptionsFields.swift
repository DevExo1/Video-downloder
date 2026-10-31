import SwiftUI

struct DownloaderPicker: View {
    @Binding var options: DownloadOptions

    var body: some View {
        Picker("Downloader", selection: $options.backend) {
            Text("Video & Audio · yt-dlp").tag(DownloadBackend.ytdlp)
            Text("Galleries · gallery-dl").tag(DownloadBackend.galleryDL)
        }
        .pickerStyle(.menu)
    }
}

struct GalleryOptionsFields: View {
    @Binding var options: DownloadOptions

    var body: some View {
        Text("Download galleries and collections in their original formats. Files are grouped in folders by site. Gallery links download directly without video format analysis.")
            .font(.callout)
            .foregroundStyle(.secondary)
        TextField("Filename template (site default if empty)", text: $options.galleryFilename)
            .autocorrectionDisabled()
            .accessibilityLabel("Gallery filename template")
        Text("Use gallery-dl keywords such as {filename}.{extension}. Available keywords depend on the site.")
            .font(.caption)
            .foregroundStyle(.secondary)
        TextField("File range, e.g. 1-20 (all if empty)", text: $options.galleryRange)
            .autocorrectionDisabled()
            .accessibilityLabel("Gallery file range")
        Toggle("Write gallery metadata JSON", isOn: $options.writeInfoJSON)
        Toggle("Skip previously archived files", isOn: $options.useDownloadArchive)
        #if os(macOS)
        if options.useDownloadArchive {
            TextField("Archive base path", text: $options.downloadArchivePath)
            Text("A separate .gallery-dl.sqlite3 archive is created at this path.")
                .font(.caption).foregroundStyle(.secondary)
        }
        Picker("Browser cookies", selection: $options.cookieBrowser) {
            ForEach(CookieBrowser.allCases) { browser in
                Text(browser.displayName).tag(browser)
            }
        }
        TextField("Cookies file path (optional)", text: $options.cookieFilePath)
        #else
        Text("Imported cookies from Settings › Cookies are used for gallery downloads too.")
            .font(.caption).foregroundStyle(.secondary)
        #endif
        TextField("Rate limit, e.g. 2M (optional)", text: $options.rateLimit)
            .autocorrectionDisabled()
        TextField("Proxy URL (optional)", text: $options.proxy)
            .autocorrectionDisabled()
        TextField("User agent (optional)", text: $options.userAgent)
            .autocorrectionDisabled()
        Toggle("ASCII filenames", isOn: $options.restrictFilenames)
        Toggle("Overwrite existing files", isOn: $options.overwriteExisting)
    }
}

# Implementation Plan: Video Downloader (Android)

See [PRD.md](PRD.md) for requirements.

## 1. Research summary
| Question | Finding |
|----------|---------|
| How to get a downloadable stream? | No official API. Two open-source routes: **yt-dlp** (Python; Android wrapper `youtubedl-android` bundles Python + yt-dlp + ffmpeg and has an in-app updater) and **NewPipeExtractor** (pure Java parser used by NewPipe). |
| Which is better for v1? | **yt-dlp via `youtubedl-android`**: widest format support, fastest to patch (update the binary without an app release), handles merging video+audio via ffmpeg. Cost: larger APK (~50-100 MB). NewPipeExtractor is a lighter fallback but needs you to write download and mux logic. |
| Current YouTube hurdles | PO tokens, SABR-only formats on the default web client, and a required external JS runtime for newer yt-dlp. Mitigation: pin to a client that works (e.g. `mweb`/`tv`), keep yt-dlp updatable, track the yt-dlp wiki. |
| Distribution | Google Play prohibits ToS-violating YouTube downloaders → ship as APK/F-Droid. |
| Opening in default player | Save via MediaStore; on tap fire `Intent.ACTION_VIEW` with the `content://` URI, MIME `video/*`, `FLAG_GRANT_READ_URI_PERMISSION`. Android 7+ forbids `file://`. |
| Background downloads | Foreground service (type `dataSync`) with notification channel; `POST_NOTIFICATIONS` on Android 13+. |

Sources: [youtubedl-android overview](https://awesome.ecosyste.ms/projects/github.com%2Finfinityloop1308%2Fyoutubedl-android), [NewPipeExtractor](https://relatedrepos.com/gh/TeamNewPipe/NewPipeExtractor), [yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide), [Play policy discussion](https://www.androidheadlines.com/2026/05/beyond-the-app-store-why-the-best-media-downloaders-arent-on-google-play.html).
Note: the search results on current yt-dlp/YouTube status were secondary and partly dated; re-verify against the yt-dlp repo before building.

## 2. Platform decision
**Native Android (Kotlin + Jetpack Compose).** The core pieces (foreground service, MediaStore, the yt-dlp wrapper, ACTION_VIEW) are all Android-native; cross-platform frameworks add a bridge layer with no benefit since iOS is out of scope.

## 3. Architecture
```
UI (Compose)  ──  ViewModels (StateFlow)
   Home screen / Library screen (tabs)
        │
Domain: UseCases (FetchInfo, EnqueueDownload, CancelDownload, DeleteVideo)
        │
Data: Room DB (downloads table) · DownloadRepository
        │
Engine: YtDlpEngine (wraps youtubedl-android) · EngineUpdater
        │
Service: DownloadService (foreground) + notification · MediaStore writer
```
- **DI:** Hilt. **Async:** Coroutines/Flow. **Images:** Coil. **DB:** Room.
- **Download flow:** insert row (QUEUED) → service picks it up → yt-dlp downloads to app cache dir with progress callback → on success, copy/move into `MediaStore.Video` (`Movies/VideoDownloader`) → row = COMPLETED with the content URI → remove temp.
- **Concurrency:** 2 simultaneous downloads (configurable); queue the rest.
- **States:** QUEUED, DOWNLOADING, PAUSED/FAILED, COMPLETED, CANCELLED.

### Data model (`downloads`)
`id, videoId, url, title, thumbnailUrl, durationSec, formatId, status, progress, bytesTotal, bytesDone, speed, etaSec, mediaStoreUri, errorMsg, createdAt, completedAt`

### Open in default player
```kotlin
val intent = Intent(Intent.ACTION_VIEW).apply {
    setDataAndType(Uri.parse(item.mediaStoreUri), "video/*")
    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
}
context.startActivity(Intent.createChooser(intent, null)) // or direct startActivity
```
Handle `ActivityNotFoundException` and a deleted-file case (URI no longer resolves → prompt to remove the entry).

## 4. Milestones
| # | Milestone | Deliverable | Est. |
|---|-----------|-------------|------|
| M0 | Project setup | Gradle project, Compose, Hilt, Room, CI build | 1-2 d |
| M1 | Engine spike | Prove `youtubedl-android` fetches info and downloads a public video on a real device; document working client/args | 2-3 d |
| M2 | Home screen | URL field, validation, metadata preview, quality picker | 2-3 d |
| M3 | Download service | Foreground service, queue, progress, notification, cancel | 3-4 d |
| M4 | Library | Downloading + Downloaded tabs, Room-backed, live progress | 2-3 d |
| M5 | MediaStore + playback | Save to Movies, tap → default player, delete | 2 d |
| M6 | Robustness | Resume/retry, process death, offline, low storage, share-sheet intake, engine updater | 3-4 d |
| M7 | Polish & release | Disclaimer screen, icons, empty/error states, signed APK, README | 2-3 d |

Total ≈ 3-4 weeks for one developer. **M1 is the go/no-go gate**: if the engine can't reliably download, nothing else matters.

## 5. Testing
- Unit: URL parsing, format selection, repository/state transitions.
- Instrumented: Room, MediaStore write/read, service lifecycle.
- Manual matrix: Android 8, 10, 13, 14+; Samsung/Pixel; default players (Google Photos, VLC, Samsung Video, MX Player); airplane-mode mid-download; kill app mid-download; low storage.
- Canary test: scheduled job downloading a known Creative Commons video to detect extractor breakage early.

## 6. Risks and mitigations
| Risk | Mitigation |
|------|------------|
| YouTube changes break extraction | In-app yt-dlp updater, canary test, pin client args remotely-configurable |
| Large APK from bundled Python/ffmpeg | ABI splits (arm64-v8a only for most users) |
| ToS / store takedown | Sideload/F-Droid distribution; first-run responsibility notice; no ads/monetisation |
| Player can't read content URI | Test matrix; fall back to chooser |
| Battery/OEM killing the service | Foreground service, notification, WorkManager resume on restart |

## 7. Next steps
1. Confirm the open questions in the PRD (distribution, scope).
2. Run **M1 spike** before committing to the full build.
3. Then scaffold M0 and proceed in order.

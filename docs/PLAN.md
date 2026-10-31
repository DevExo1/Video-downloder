# Implementation Plan: Video Saver for iPhone

See [PRD.md](PRD.md). Replaces the v0.2 React Native + server plan. iOS only, fully on-device.

## 1. Research summary
| Option | What it is | Verdict |
|--------|-----------|---------|
| **A. yt-dlp embedded in the app** | CPython 3.14 (official iOS support since 3.13, packaged by BeeWare) running yt-dlp in-process; JavaScriptCore solves YouTube's JS challenges; AVFoundation replaces ffmpeg | **Chosen.** Proven by [PopShark57/ytdlp-gui PR #3](https://github.com/PopShark57/ytdlp-gui/pull/3) (merged 2026-09-25, live YouTube tests passing). Most maintained extractor; updatable without rebuilding. |
| B. [YouTubeKit](https://github.com/alexeichhorn/YouTubeKit) (Swift, MIT) | Native Swift extractor returning stream URLs; optional remote fallback server | Fallback / quick prototype. Simpler and smaller, but a much smaller team than yt-dlp fixing breakage, and its robust mode uses a server. |
| C. [YoutubeDL-iOS](https://github.com/kewlbear/YoutubeDL-iOS) | Older Swift wrapper for yt-dlp | Skip: predates the JS-runtime requirement, little activity. |
| D. WebView capture | Record the real player's stream | Rejected (fragile, real-time, foreground-only). |
| E. Server | Download on a server | Rejected per owner (no server). |

Key technical facts:
- Since yt-dlp 2025.11.12, full YouTube support needs a JavaScript runtime plus the `yt-dlp-ejs` scripts ([announcement](https://github.com/yt-dlp/yt-dlp/issues/15012), [EJS](https://github.com/yt-dlp/ejs)). Deno/Node/Bun don't exist on iOS, and subprocesses aren't allowed, so we register a **custom EJS provider backed by JavaScriptCore** (`jsc`). Both the PopShark app and [yt-dlp-ios](https://github.com/yousif-toama/yt-dlp-ios) do this successfully.
- PO tokens: yt-dlp-ios mints them with `bgutils-js` in a hidden WKWebView, with a `visionos` client fallback that needs neither PO token nor JS. Adopt the same if the default clients start failing.
- Muxing: yt-dlp's merger/postprocessors are replaced by AVFoundation (passthrough export of H.264 video + AAC audio into .mp4, no re-encoding).
- [Python on iOS docs](https://docs.python.org/3/using/ios.html), [BeeWare Python-Apple-support](https://github.com/beeware/Python-Apple-support).

## 2. Tech stack
| Layer | Choice |
|-------|--------|
| App | **Swift + SwiftUI** (React Native adds a bridge and nothing else for an iOS-only app whose core is native) |
| Python | BeeWare `Python.xcframework` (CPython 3.14), embedded |
| Engine | yt-dlp + yt-dlp-ejs (pure-Python wheels), bundled and updatable |
| JS challenges | JavaScriptCore via custom yt-dlp EJS provider plugin |
| Merge | AVFoundation (`AVMutableComposition` + `AVAssetExportSession` passthrough) via a yt-dlp postprocessor plugin |
| Storage | Files in app `Documents/Videos`; metadata in SwiftData |
| Player | `AVPlayerViewController` |
| Share intake | Share Extension + App Group (needs paid account) |
| Background | `URLSession`-free; yt-dlp downloads in-process → `BGContinuedProcessingTask` (iOS 26+) to keep going after backgrounding |

## 3. Architecture
```
SwiftUI
  HomeView (URL field, Paste, Save)
  DownloadsView ── tabs: Downloading | Saved ── PlayerView
        │
DownloadManager (Swift, @Observable, queue of jobs, 1 at a time)
        │  JSON over C bridge
PythonHost (embedded CPython thread)
  host.py: run yt-dlp with options, stream progress events back
  plugins/jsc_provider.py   → calls Swift → JavaScriptCore
  plugins/avf_merger.py     → calls Swift → AVFoundation merge
        │
Files: Documents/Videos/<id>.mp4 + thumbnail · SwiftData record
EngineUpdater: fetch latest yt-dlp wheel from GitHub/PyPI → Application Support/engine (overrides bundled copy)
```
yt-dlp options (starting point): `format = bv*[vcodec^=avc1][height<=1080]+ba[acodec^=mp4a]/b[ext=mp4]`, `merge_output_format = mp4`, `noplaylist = true`, progress hooks → Swift.

## 4. Milestones
| # | Milestone | Deliverable | Est. |
|---|-----------|-------------|------|
| M0 | Setup | Xcode project, SwiftUI shell, signing, scripts to fetch Python.xcframework + wheels (pinned, SHA-checked) | 1-2 d |
| M1 | **Engine spike (go/no-go)** | On a real iPhone: Python starts, yt-dlp extracts info for a public video, JSC solves challenges, a progressive (single-file) download completes | 3-4 d |
| M2 | Merge | AVFoundation merger plugin; 1080p video+audio → playable .mp4 | 2-3 d |
| M3 | UI | Home (URL/Paste/Save), Downloads tabs, progress, cancel, delete, player | 3-4 d |
| M4 | Persistence + errors | SwiftData library, restart-safe, error messages | 2 d |
| M5 | Engine updater | In-app "Update engine", version shown in Settings, rollback to bundled | 2 d |
| M6 | Extras | Share Extension, export to Photos/Files, background continuation | 3-4 d |
| M7 | Release | First-run notice, icon, install on your devices, README with build/install steps | 1-2 d |

Total ≈ 3-4 weeks for one developer. If M1 fails, fall back to YouTubeKit (option B) for extraction and keep the same UI.

**Shortcut:** the PopShark57/ytdlp-gui iOS code is open source. M0-M2 can start by studying (and, license permitting, reusing) its Python bridge, JSC provider and AVFoundation merger. Check its license before copying code.

## 5. Testing
- Unit: URL validation, job state machine, file store.
- Integration (on device): download a known Creative Commons video daily during development as a canary.
- Manual: short video, 1-hour video, Shorts, Wi-Fi ↔ cellular switch, airplane mode mid-download, app killed mid-download, low storage, background/lock screen.

## 6. Install on your iPhones (no App Store)
| Method | Needs | Expiry | Notes |
|--------|-------|--------|-------|
| Xcode direct install, **paid** Developer account ($99/yr) | Mac + Xcode, register device UDIDs (≤100) | 1 year | **Recommended.** Share Extension works. |
| TestFlight internal testers | Paid account | 90 days per build | Up to 100 App Store Connect users; easiest for others to install |
| Xcode with **free** Apple ID | Mac + Xcode | 7 days | No App Groups → no Share Extension; re-install weekly (or use SideStore/AltStore to refresh) |

A Mac with Xcode is required for building in all cases.

## 7. Next steps
1. Confirm: paid Apple account? iOS version on target phones? Mac available?
2. Run the **M1 spike** on a real iPhone.
3. Build M2-M7.

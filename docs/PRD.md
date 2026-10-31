# PRD: Video Downloader (React Native, Android + iOS, private)

Status: Draft v0.2 · Owner: devexo1
Changes from v0.1: cross-platform (React Native), private distribution, server-assisted architecture.

## 1. Summary
A private phone app (Android + iPhone) where the user pastes a YouTube URL, downloads the video to the device, and later plays it. Two areas: **Home** (URL input) and **Library** (Downloading / Downloaded tabs). Extraction is done by a small self-hosted backend; the phone app downloads the finished file from it.

## 2. Goals
- Paste a URL, see title/thumbnail/duration, pick a quality, tap Download.
- Live progress for active downloads, with cancel/retry.
- Downloaded list; tapping an item opens the video in the phone's native player experience (see §7 for the iOS difference).
- Downloads continue in the background where the OS allows.
- Single TypeScript codebase for both platforms.

## 3. Non-goals (v1)
- Public App Store / Google Play release (private distribution only).
- Multi-user accounts, payments, ads, analytics.
- Age-restricted, private, DRM or paid content; YouTube sign-in.
- In-app player (v1 hands off to the OS).
- Sites other than YouTube in the UI (backend supports more).

## 4. Users and distribution
- Users: the owner and a small invited group (family/friends). Order of tens of users, not thousands.
- **Android:** signed APK sideload (or internal link).
- **iOS:** TestFlight (up to 10,000 testers, builds expire every 90 days; needs paid Apple Developer account, $99/yr) or Ad Hoc (up to 100 registered devices/yr, no expiry per build beyond the profile year). Enterprise distribution is not appropriate for friends/family use.

## 5. User stories
1. Paste a YouTube link (or Share → app) and see a preview.
2. Pick quality (1080p/720p/480p/audio-only) and start the download.
3. See progress, speed, ETA; cancel or retry.
4. Open the Downloaded tab and tap a video to play it.
5. Delete a downloaded video.
6. First launch: enter server URL + access token once.

## 6. Functional requirements
| ID | Requirement | Pri |
|----|-------------|-----|
| F1 | URL input with paste button; validate youtube.com / youtu.be / shorts / music links | P0 |
| F2 | Preview via backend `/info` (title, thumbnail, duration, formats) | P0 |
| F3 | Quality picker; default best ≤1080p MP4 (H.264/AAC for universal playback) | P0 |
| F4 | Job flow: app requests job → backend downloads/merges → app downloads the file → file saved on device | P0 |
| F5 | Library with **Downloading** tab (server-side preparing + device transfer progress, cancel/retry) and **Downloaded** tab (thumbnail, title, size, duration) | P0 |
| F6 | Tap downloaded item → open in native player (Android: system default via `ACTION_VIEW`; iOS: see §7) | P0 |
| F7 | Persistent library (local DB) surviving restarts | P0 |
| F8 | Backend auth via static bearer token over HTTPS | P0 |
| F9 | Delete item (file + record), long-press/swipe | P1 |
| F10 | Resume interrupted transfers (HTTP Range) | P1 |
| F11 | Share-sheet intake (Android intent filter, iOS Share Extension) | P1 |
| F12 | Background transfer continues when app is backgrounded | P1 |
| F13 | Audio-only option | P2 |
| F14 | Server auto-delete of finished files after N hours | P1 |

## 7. Platform differences (important)
- **Android:** save to `Movies/VideoDownloader` via MediaStore; tap launches `ACTION_VIEW` with a `content://` URI → true system default player.
- **iOS has no "default video player" setting.** Options, chosen in this order:
  1. Save to the **Photos library** (needs add-only permission) and open with the system **QuickLook / share sheet** ("Open in VLC", "Save to Files", etc.). **Recommended:** tap shows QuickLook preview (native full-screen player) with a share button.
  2. Alternative: present the iOS share sheet / "Open in…" directly.
  This is the closest equivalent; the PRD requirement "opens in default player" is satisfied on Android literally and on iOS via the native player + share sheet.
- iOS background downloads are managed by the OS (background URLSession); they can be delayed and the app is not guaranteed to run. Android uses a foreground service for reliability.

## 8. Non-functional requirements
- Android 8+ (API 26); iOS 16+.
- React Native (TypeScript), new architecture; **Expo with development builds** (not Expo Go, native modules needed).
- Backend: Docker container (yt-dlp + ffmpeg + small HTTP API), HTTPS, token auth, rate limiting.
- No analytics; data stays between the phone and the owner's server.
- Crash-free sessions ≥ 99%; ≥ 90% of valid public URLs download successfully.

## 9. Architecture decision: why a backend
On Android, yt-dlp can run on-device (`youtubedl-android`). On iOS there is no maintained, App-Store-quality way to run yt-dlp (needs embedded Python + ffmpeg, no JIT, no subprocesses). To get one codebase on both platforms, extraction and merging run on a **server the owner controls**, and both apps behave identically as thin clients. Side benefits: fix YouTube breakage by updating one container, not two apps.

Trade-offs the owner accepts:
- Requires a running server (cost/uptime). A **home server or residential IP** works best; cloud datacenter IPs are often challenged or blocked by YouTube (bot checks / PO-token requirements).
- Traffic goes phone → server → phone (server bandwidth matters).
- Server holds the legal exposure of fetching content (see §10).

## 10. Risks and constraints
1. **Terms of Service / copyright.** YouTube's Terms prohibit downloading except via provided features. Private use limits visibility but doesn't remove the issue. Only download content you have rights to; include a first-run notice. Keep the app and server private and non-commercial.
2. **Store policy.** Public App Store / Play listing would be rejected; that is why distribution is private (TestFlight/Ad Hoc/APK). TestFlight external testing still goes through Apple beta review, so keep the app generic ("personal media saver") and honest; internal testers (up to 100 App Store Connect users) skip review.
3. **Extractor breakage.** No official API; PO tokens, SABR and JS-runtime requirements change often. Mitigation: pinned + auto-updating yt-dlp in the container, canary job, PO-token provider sidecar if needed. ([yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide))
4. **iOS 90-day TestFlight expiry** → rebuild and re-upload quarterly (automate with EAS).
5. **iOS storage:** large files in Photos/Files; need disk-space checks.
6. **Server security:** exposed endpoint that fetches arbitrary URLs → restrict to YouTube hosts, token auth, rate limit, no open proxy behavior.

## 11. Open questions
- Where will the server run (home machine, VPS, Raspberry Pi)? Affects IP-blocking risk.
- iOS distribution: TestFlight (simplest) or Ad Hoc? Do you already have an Apple Developer account?
- Is the iOS "QuickLook + share sheet" answer acceptable for the "open in player" requirement?
- Number of users / devices?

# PRD: Video Downloader (Android)

Status: Draft v0.1 · Owner: devexo1

## 1. Summary
A phone app where the user pastes a YouTube URL, downloads the video to the device, and later plays it in the phone's default video player. Two screens/tabs: **Home** (URL input) and **Library** (Downloading / Downloaded).

## 2. Goals
- Paste a URL, see title and thumbnail, choose a quality, tap Download.
- Show live progress for active downloads, with pause/cancel/retry.
- List finished downloads; tapping one opens it in the system's default video player.
- Downloads keep running when the app is in the background.

## 3. Non-goals (v1)
- iOS (Apple sandboxing and App Store rules make this impractical; revisit later).
- Google Play distribution (see Risks).
- Built-in video player, accounts, cloud sync, ads.
- Age-restricted, private, DRM or paid content.
- Sites other than YouTube (the engine supports more; UI can follow later).

## 4. Target user
An individual who wants offline copies of videos they have the right to keep (own uploads, Creative Commons, permission granted).

## 5. User stories
1. As a user, I paste a YouTube link (or share it to the app from YouTube) and see a preview.
2. As a user, I pick quality (e.g. 1080p / 720p / 480p / audio-only) and start the download.
3. As a user, I see progress, speed and ETA, and can cancel or retry.
4. As a user, I open the Downloaded tab and tap a video to play it in my default player.
5. As a user, I can delete a downloaded video.

## 6. Functional requirements
| ID | Requirement | Priority |
|----|-------------|----------|
| F1 | URL text field with paste button; validate youtube.com / youtu.be / shorts / music links | P0 |
| F2 | Fetch metadata (title, thumbnail, duration, available formats) before download | P0 |
| F3 | Quality picker with sensible default (best ≤1080p MP4) | P0 |
| F4 | Download runs as a foreground service with a notification and progress | P0 |
| F5 | Library screen with two tabs: **Downloading** (progress, cancel/retry) and **Downloaded** (thumbnail, title, size, duration) | P0 |
| F6 | Tap a downloaded item → launch `ACTION_VIEW` with `video/*` so the system default player opens; chooser if no default is set | P0 |
| F7 | Video saved to shared storage (`Movies/VideoDownloader`) via MediaStore so it also shows in Gallery | P0 |
| F8 | Handle Android share-sheet "Share → Video Downloader" | P1 |
| F9 | Delete item (removes file + record), swipe or long press | P1 |
| F10 | Resume after app kill / reboot / connectivity loss | P1 |
| F11 | Audio-only (m4a/mp3) option | P2 |
| F12 | Playlist download | P2 |
| F13 | In-app engine updater (see Risks) | P0 |

## 7. UX
- **Bottom navigation:** Home · Library.
- **Home:** URL field, Paste button, Fetch → preview card (thumbnail, title, duration) → quality dropdown → Download button. Snackbar "Added to downloads" with a View action.
- **Library:** top tabs *Downloading* / *Downloaded*. Empty states for each. Downloading rows show progress bar, %, speed, ETA, cancel. Downloaded rows show thumbnail, title, size; tap plays.
- Error states: invalid URL, no network, video unavailable/private/age-gated, low storage, extraction failed ("Update engine and retry").

## 8. Non-functional requirements
- Android 8.0+ (API 26+), target current SDK.
- Cold start < 2 s; metadata fetch typically < 5 s on good network.
- No crashes on process death during download; state restored from DB.
- Permissions: INTERNET, FOREGROUND_SERVICE (+ data-sync type), POST_NOTIFICATIONS. No broad storage permission (MediaStore scoped storage).
- No analytics or tracking in v1; no user data leaves the device.

## 9. Success metrics
- ≥ 90% of valid public-video URLs download successfully.
- Time from paste to download start < 10 s.
- Crash-free sessions ≥ 99%.

## 10. Risks and constraints (read this)
1. **Terms of Service / legality.** YouTube's Terms prohibit downloading content except through features YouTube provides (e.g. YouTube Premium offline), and copyrighted content may not be copied without permission. The app should present a clear first-run notice that users are responsible for only downloading content they have rights to. The developer carries the legal risk of distributing such a tool.
2. **Google Play.** Google's Developer Program Policy (Device and Network Abuse) forbids apps that download YouTube videos in violation of its terms; downloader apps are commonly rejected or removed. Plan on **direct APK / F-Droid-style distribution**, not Play. ([discussion](https://www.androidheadlines.com/2026/05/beyond-the-app-store-why-the-best-media-downloaders-arent-on-google-play.html))
3. **Breakage risk.** There is no official download API. YouTube changes its player frequently, and recent changes (PO tokens, SABR streaming, a required external JavaScript runtime) have broken extractors. Expect ongoing maintenance and ship an in-app engine updater. ([yt-dlp PO Token Guide](https://github.com/yt-dlp/yt-dlp/wiki/PO-Token-Guide))
4. **Format limits.** Some high-quality or DRM'd formats may be unavailable without sign-in; v1 does not support login.
5. **Third-party player compatibility.** Content URI grants behave differently across players; needs testing on several devices/players.

## 11. Open questions
- Distribution target: sideloaded APK only, or also F-Droid/own site?
- Is personal use only the intended scope? (Affects the in-app disclaimer wording.)
- Should v1 include share-sheet intake (F8)?
- Android only, or will iOS be needed later?

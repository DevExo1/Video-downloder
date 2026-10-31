# PRD: Video Saver for iPhone (private)

Status: Draft v0.4 · Owner: devexo1
v0.4: v1 is a fork of the MIT-licensed open-source app PopShark57/ytdlp-gui (see PLAN.md).
Changes from v0.2: **iOS only**, **no server**, everything runs on the phone. Android is deferred.

## 1. Summary
A private iPhone app: the user pastes a YouTube URL, taps Save, and the video is downloaded onto the phone. Saved videos appear in a list and play in the iPhone's native video player. All work happens on-device; there is no backend.

## 2. Goals
- Paste a URL → Save → video file on the phone. That is the core.
- See what is downloading and what is saved.
- Tap a saved video to play it (native iOS player); optionally save it to Photos or Files.
- Keep working when YouTube changes things, by updating the download engine without rebuilding the app.

## 3. Non-goals (v1)
- Android (later; the engine choice below also exists for Android).
- App Store release.
- Playlists, channels, audio-only, subtitles, sign-in, age-restricted/private/paid videos.
- Any server or cloud component.

## 4. Users and distribution
- The owner and a few people they trust. Sideloaded, not public.
- Install options (pick one, see PLAN §6): paid Apple Developer account direct install (1-year profile) · TestFlight internal testers · free Apple ID (re-sign every 7 days).

## 5. User stories
1. I paste a YouTube link (or share it from the YouTube app) and tap **Save**.
2. I see it in **Downloading** with progress, and can cancel.
3. When finished it moves to **Saved**; I tap it and it plays.
4. I can delete it, or export it to Photos / Files.

## 6. Functional requirements
| ID | Requirement | Pri |
|----|-------------|-----|
| F1 | URL field + Paste button; accept youtube.com, youtu.be, shorts, m.youtube.com links | P0 |
| F2 | Save button: fetch info + download best MP4 up to 1080p (H.264 + AAC so iOS plays it natively) | P0 |
| F3 | Merge separate video and audio streams on-device into one .mp4 | P0 |
| F4 | **Downloads** screen with two tabs: *Downloading* (title, progress %, cancel) and *Saved* (thumbnail, title, duration, size) | P0 |
| F5 | Tap a saved video → full-screen native iOS player | P0 |
| F6 | Saved files persist across app restarts (app Documents folder, visible in the Files app) | P0 |
| F7 | Delete a saved video | P0 |
| F8 | Clear error messages: invalid link, no internet, video unavailable, engine needs update | P0 |
| F9 | "Update engine" action: downloads the latest yt-dlp release into the app | P0 |
| F10 | Share sheet: "Share → Video Saver" from the YouTube app | P1 |
| F11 | Export to Photos / Save to Files | P1 |
| F12 | Keep downloading for a while after the app is backgrounded | P1 |
| F13 | Quality choice (1080p / 720p / 480p) | P2 |

## 7. Non-functional requirements
- iOS 18+ (required by the base app; iOS 26+ for extended background downloading, F12).
- Native Swift/SwiftUI app; no server, no analytics, no data leaves the phone except requests to YouTube.
- A 10-minute 1080p video should save in roughly the time the network allows (no real-time playback needed).
- App size target < 120 MB (embedded Python runtime is the bulk).

## 8. How it works (plain language)
yt-dlp is the most actively maintained YouTube downloader. It is written in Python. iPhones can't run separate programs, but since Python 3.13, Python is officially supported as a library **inside** an iOS app. So the app bundles Python and yt-dlp and calls them directly. The pieces yt-dlp normally borrows from the computer are replaced with what iOS already has:
- **JavaScript** (YouTube's anti-bot puzzles) → Apple's built-in JavaScriptCore.
- **ffmpeg** (joining video + audio) → Apple's AVFoundation.
An open-source iOS app already does exactly this and passed live YouTube tests in September 2026 ([PopShark57/ytdlp-gui PR #3](https://github.com/PopShark57/ytdlp-gui/pull/3)), so this is proven, not theoretical.

Why this lasts: when YouTube changes, the yt-dlp team typically ships a fix within days. Because yt-dlp is Python code, the app can download the new version and use it immediately, with no rebuild.

## 9. Risks
1. **Terms of Service / copyright.** YouTube's Terms forbid downloading outside its own features. Private use doesn't change that. Only save content you have the right to keep; the app shows this on first launch.
2. **YouTube anti-bot changes** (PO tokens, JavaScript challenges). Mitigated by the in-app engine update; may occasionally need app-side changes too.
3. **Distribution friction.** Free Apple ID installs expire every 7 days; paid account ($99/yr) gives 1-year installs.
4. **Background limits.** iOS may pause downloads when the app is in the background on older iOS versions.
5. **Young ecosystem.** The JavaScriptCore and AVFoundation replacements are newer and less battle-tested than the desktop setup.

## 10. Open questions
- Do you have (or want) a paid Apple Developer account? It decides the install method.
- Minimum iOS version on your phones?
- Is 1080p the right ceiling? (Higher resolutions are usually VP9/AV1, which iPhones play less reliably.)

# Implementation Plan: Video Saver for iPhone

See [PRD.md](PRD.md). iOS only, fully on-device. **v0.4: start from an existing open-source app instead of building from scratch.**

## 1. Strategy: fork, ship, then extend
[PopShark57/ytdlp-gui](https://github.com/PopShark57/ytdlp-gui) is a native iPhone/iPad (and macOS) front end for yt-dlp that already does what our PRD's core needs, entirely on-device:
- CPython 3.14 embedded (BeeWare `Python.xcframework`), yt-dlp running in-process.
- YouTube JavaScript challenges solved with Apple's JavaScriptCore (custom EJS provider `jsc`).
- ffmpeg replaced by AVFoundation (merging, audio conversion, metadata).
- Save to Photos, Files integration, Share extension, background continuation (iOS 26+), in-app yt-dlp updates.
- iOS work merged 2026-09-25 with on-device tests passing ([PR #3](https://github.com/PopShark57/ytdlp-gui/pull/3)).

**License: MIT** → we may fork, modify and use it privately. Obligation: keep its `LICENSE` file and copyright notice. The bundled yt-dlp is Unlicense (public domain); CPython and other wheels keep their own licenses.

So v1 = **our fork, built and installed as-is**. We only write code where it falls short of the PRD.

### Things to know about the upstream project
| Fact | Implication |
|------|-------------|
| One maintainer, 0 stars, young project | Don't depend on them for fixes; our fork must stand on its own. Keep an `upstream` remote and pull useful changes when they appear. |
| Requires iOS/iPadOS 18+, Xcode 16+ | Target phones must be on iOS 18 or later. |
| Also includes macOS app and gallery-dl | Extra code we don't need; can leave it or trim later. |
| Untested on device per its PR: Share extension UI, background continuation, Save to Photos, engine update, Release build | These are the first things we verify. |
| Free Apple account: no App Groups → Share extension disabled, app stops launching after 7 days | Paid account recommended (see §5). |

## 2. Milestones
| # | Milestone | What happens | Est. |
|---|-----------|--------------|------|
| M0 | **Fork** | Fork into `devexo1` on GitHub; add `upstream` remote; this repo keeps our docs (or move them into the fork) | 0.5 d |
| M1 | **Build & install as-is** | On a Mac: `./Tools/fetch-ios-dependencies.sh` → open `YTDLPGUI.xcodeproj` → scheme `YTDLPGUI-iOS` → set your Team → run on your iPhone | 0.5-1 d |
| M2 | **Acceptance test against PRD** | Run the checklist in §3 on a real iPhone; record what passes, fails, or is missing | 1 d |
| M3 | **Gap list → backlog** | Turn failures/missing items into issues, prioritised (P0 first) | 0.5 d |
| M4+ | **Extend** | Implement only the gaps we need (examples in §4), one small PR each | as needed |

**First usable build: about 2-3 days**, versus 3-4 weeks from scratch.

## 3. Acceptance checklist (run in M2)
Mapped to PRD requirements. Use a public video you have the right to keep (e.g. a Creative Commons upload).
- [ ] F1 Paste a youtube.com, youtu.be and Shorts link → accepted
- [ ] F2/F3 Save → 1080p MP4 with sound, plays in the iPhone player
- [ ] F4 Progress visible while downloading; cancel works
- [ ] F5 Tap saved item → plays
- [ ] F6 Files persist after app restart; visible in Files app
- [ ] F7 Delete works
- [ ] F8 Sensible error for bad link / airplane mode
- [ ] F9 Engine update works
- [ ] F10 Share from YouTube app → download starts (paid account only)
- [ ] F11 Save to Photos works
- [ ] F12 Download continues after leaving the app (iOS 26+)
- [ ] Long video (≥ 1 h), Shorts, airplane mode mid-download, low storage

## 4. Likely extensions (only if the checklist shows a need)
- **Simplified UI**: a single "paste and Save" home screen plus Downloading/Saved tabs, if the upstream UI is more complex than we want.
- **Defaults**: preset to best H.264/AAC MP4 ≤1080p so every file plays natively.
- **Rebrand**: our app name, icon, bundle ID.
- **Trim**: remove gallery-dl and macOS targets if they get in the way.
- **First-run notice** about only saving content you have the right to keep.
- **Android** later (separate app; Android can run yt-dlp via `youtubedl-android`).

## 5. Install on your iPhones (no App Store)
| Method | Needs | Expiry | Notes |
|--------|-------|--------|-------|
| Xcode direct install, **paid** Developer account ($99/yr) | Mac + Xcode, device registered | 1 year | **Recommended.** Share extension works. |
| TestFlight internal testers | Paid account | 90 days per build | Easiest way to give it to others |
| Xcode with **free** Apple ID | Mac + Xcode | 7 days | No Share extension; reinstall weekly |

A Mac with Xcode 16+ is required in every case. The App Store is not an option (App Review Guideline 5.2.3).

## 6. Fallback
If the fork can't be made to work on our devices, fall back to building our own app (previous plan v0.3: same architecture, built from scratch) or using [YouTubeKit](https://github.com/alexeichhorn/YouTubeKit) for extraction.

## 7. Next steps
1. Confirm: Mac with Xcode 16+? Paid Apple account? Phones on iOS 18+?
2. Approve forking `PopShark57/ytdlp-gui` into your GitHub account.
3. Build M1 on your Mac and run the M2 checklist; I'll turn results into the backlog.

# Build and install on your iPhone (Mac steps)

One-time setup takes about 15-30 minutes. You need: Mac with Xcode 16+, your iPhone (iOS 18+; you are on 27), a USB cable, and the paid Apple Developer account (team `4BUWFMA7GQ`, already set in the project).

## 1. Get the code
In Terminal:
```bash
git clone https://github.com/DevExo1/Video-downloder.git
cd Video-downloder
git checkout claude/video-downloader-plan
```

## 2. Download Python and yt-dlp (once)
```bash
./Tools/fetch-ios-dependencies.sh
```
It downloads the embedded Python runtime and yt-dlp, checks each file's checksum, and puts them in `Vendor/` (not committed). It ends without errors when done.

## 3. Prepare the iPhone (once)
1. Plug the iPhone into the Mac, unlock it, tap **Trust**.
2. On the iPhone: **Settings › Privacy & Security › Developer Mode** → on, then restart the phone when asked.

## 4. Build and run
1. Open `YTDLPGUI.xcodeproj` in Xcode.
2. At the top of the window choose the scheme **YTDLPGUI-iOS** and your iPhone as the destination.
3. Xcode › **Settings › Accounts**: make sure your Apple ID is signed in.
4. Press **Run** (▶). The first build takes a few minutes.
   - If Xcode shows a signing error, select the **YTDLPGUI-iOS** target › **Signing & Capabilities**, tick **Automatically manage signing**, choose your team, and press Run again. Do the same for **YTDLPGUI-iOS-Share**.
5. The app opens on your iPhone. If iOS says the developer is untrusted: **Settings › General › VPN & Device Management** → your developer profile → **Trust**.

## 5. Test
Run the checklist in [PLAN.md §3](PLAN.md#3-acceptance-checklist-run-in-m2) and tell me what passes and fails. Anything that goes wrong, copy the error text (or a screenshot) back to me.

## Notes
- Bundle IDs were changed from the original author's `io.github.ytdlpgui.*` to `com.devexo1.ytdlpgui.*` (Apple IDs must be unique per team). The app is still called "YTDLP GUI"; naming is decided later.
- Upstream source: https://github.com/PopShark57/ytdlp-gui (MIT). Its `LICENSE` is kept at the repo root. The iOS app also bundles gallery-dl (GPL-2.0) — fine for private use; it can be removed later.
- The installed app keeps working for a year (profile lifetime); rebuild from Xcode to renew.

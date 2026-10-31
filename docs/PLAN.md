# Implementation Plan: Video Downloader (React Native + backend)

See [PRD.md](PRD.md). This replaces the v0.1 native-Android plan.

## 1. Key decisions
| Decision | Choice | Why |
|----------|--------|-----|
| Mobile framework | React Native + TypeScript via **Expo (dev builds + EAS Build)** | One codebase; EAS handles iOS signing/TestFlight; native modules allowed |
| Extraction | **Self-hosted backend** running yt-dlp + ffmpeg | yt-dlp can't practically run on iOS; same behavior on both platforms |
| Backend stack | Node (Fastify) or Python (FastAPI) in Docker | FastAPI is the natural fit: calls yt-dlp as a library; Node is fine if you prefer one language. **Recommend FastAPI.** |
| Transfer | Backend serves finished file over HTTPS with Range support | Resumable, works with OS background downloaders |
| Local state | SQLite (`expo-sqlite`) + Zustand/React Query | Persistent library, simple UI state |
| Navigation | Expo Router, bottom tabs: Home, Library | Matches PRD |
| Distribution | Android APK (EAS) · iOS TestFlight (internal testers) | Private app |

Library choices below are my recommendations from memory, **not verified against current versions**; confirm each in the M1 spike.

## 2. Architecture
```
 Phone (RN app)                         Your server (Docker)
 ┌──────────────────────┐   HTTPS+token  ┌────────────────────────┐
 │ Home: URL → /info    │ ─────────────► │ FastAPI                │
 │ Library tabs         │                │  POST /info            │
 │ Job poller           │ ◄───────────── │  POST /jobs            │
 │ Background downloader│   GET /files   │  GET  /jobs/{id}       │
 │ SQLite + file store  │ ◄───────────── │  GET  /files/{id} (Range)
 └──────────────────────┘                │ yt-dlp + ffmpeg worker │
                                         │ temp storage + cleanup │
                                         └────────────────────────┘
```

### Job lifecycle
`QUEUED → PREPARING (server downloads/merges) → READY → TRANSFERRING (phone pulls file) → SAVED` · or `FAILED / CANCELLED` at any step.
- The **Downloading** tab shows both server-side preparing (indeterminate or % from yt-dlp progress) and phone-side transfer progress.
- Server deletes a file after the phone confirms receipt (`DELETE /jobs/{id}`) or after a TTL.

### Backend API (v1)
| Endpoint | Purpose |
|----------|---------|
| `POST /info {url}` | title, thumbnail, duration, format options |
| `POST /jobs {url, formatPreset}` | create job → `{id}` |
| `GET /jobs/{id}` | `{status, progress, filesize, error}` |
| `DELETE /jobs/{id}` | cancel / cleanup |
| `GET /files/{id}` | stream file, supports `Range` |
Auth: `Authorization: Bearer <token>`; only YouTube hostnames accepted; per-token rate limit; request body size limits.

### Mobile modules (recommended; verify in M1)
- Transfer with background support: `@kesha-antonov/react-native-background-downloader` (iOS background URLSession + Android) — fallback `expo-file-system` resumable downloads (foreground only).
- Save to device: `expo-media-library` (Android MediaStore `Movies/`, iOS Photos add-only).
- Open video:
  - Android: `expo-intent-launcher` / `react-native-blob-util` `actionViewIntent` with a `content://` URI + `video/mp4` → system default player.
  - iOS: QuickLook via `react-native-file-viewer` (or `expo-sharing` share sheet).
- Share intake: `expo-share-intent` (config plugin handles Android intent filter + iOS Share Extension).
- Secrets: server URL + token in `expo-secure-store`.

### Project layout
```
/app            Expo Router screens (home, library/[downloading|downloaded])
/src/api        server client + types
/src/db         SQLite schema + repos
/src/transfer   background downloader wrapper, resume logic
/src/player     openVideo.ts (platform split: .android.ts / .ios.ts)
/server         FastAPI app, Dockerfile, docker-compose.yml
/docs
```

## 3. Milestones
| # | Milestone | Deliverable | Est. |
|---|-----------|-------------|------|
| M0 | Repo setup | Monorepo (`app/`, `server/`), TS, lint, EAS config, CI | 2 d |
| M1 | **Spikes (go/no-go)** — (a) server: yt-dlp downloads a public video from the intended host/IP; (b) phone: background download of a large file on real iPhone + Android; (c) iOS save-to-Photos + QuickLook; (d) Android open via content URI | Written results; library choices confirmed | 4-5 d |
| M2 | Backend v1 | `/info`, `/jobs`, `/files`, auth, Docker image, cleanup, canary test | 4-5 d |
| M3 | Home screen | URL field, paste, validation, preview, quality picker | 2-3 d |
| M4 | Transfer + Library | Job poller, background download, SQLite, Downloading/Downloaded tabs | 5-6 d |
| M5 | Save + play | MediaLibrary save, Android default player, iOS QuickLook/share, delete | 3 d |
| M6 | Robustness | Resume, retries, offline, low storage, app-kill recovery, share intake, settings screen (server URL/token) | 4-5 d |
| M7 | Release | Disclaimer, icons, Android APK, iOS TestFlight build, server deploy docs | 3-4 d |

Total ≈ 5-6 weeks for one developer. **M1 is the gate**: if the server IP gets blocked by YouTube or iOS background transfer is unreliable, revisit (home server/residential IP, proxy, or foreground-only transfers).

## 4. Testing
- Server: unit tests on URL allow-list, job state machine; integration test against a Creative Commons video; **daily canary** that alerts when extraction fails.
- App: unit (Jest) for URL parsing, DB, job reducer; E2E (Maestro or Detox) for paste → download → open.
- Manual matrix: iPhone (iOS 16/17/18) + Android 8/10/13/14; Wi-Fi/cellular switch; airplane mode mid-transfer; kill app mid-transfer; large (>1 GB) file; low storage.

## 5. Deployment
- Server: `docker compose up` with Caddy/Traefik for automatic HTTPS (or Tailscale to avoid public exposure — **recommended** for a private app; phones then reach the server over the tailnet and no public endpoint exists).
- yt-dlp auto-update on container start + nightly; optional PO-token provider sidecar if YouTube requires it.
- EAS Build for both platforms; TestFlight via `eas submit`; set a calendar reminder for the 90-day TestFlight expiry (or automate).

## 6. Risks and mitigations
| Risk | Mitigation |
|------|------------|
| YouTube blocks server IP | Run on home/residential connection; cookies are out of scope; proxy as fallback |
| Extractor breakage | Nightly yt-dlp update, canary, pinned known-good fallback image |
| iOS background transfers throttled | Set expectations in UI; resume on foreground; Range requests |
| iOS "default player" mismatch | QuickLook + share sheet; documented in PRD §7 |
| Apple beta review of TestFlight external builds | Use internal testers; generic app name/description |
| Server abuse if token leaks | Tailscale-only access, rotate token, rate limits, host allow-list |
| ToS/copyright | Private, non-commercial, first-run notice, user responsibility |

## 7. Next steps
1. Answer the PRD open questions (server location, Apple account, iOS player behavior).
2. Run **M1 spikes** (server fetch from your actual network; phone background transfer).
3. Scaffold M0 and proceed in order.

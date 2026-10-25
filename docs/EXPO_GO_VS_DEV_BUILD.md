# Expo Go vs development build — what works where (SDK 58)

The owner opens the mobile app through **Expo Go** (`exp://<LAN-IP>:8082`). Some required features cannot run there. This table is binding: build everything so the app **boots and is usable in Expo Go**, mark each feature that needs a development build with `requires: dev-build` in code and in `docs/PREFLIGHT.md`, and never fake it.

| Capability | Expo Go | Dev build / release | Rule |
|---|---|---|---|
| Floating pill tab bar (`expo-router/ui`) | Yes | Yes | Core; must work in Expo Go. |
| `expo-symbols` (SF Symbols iOS / Material Symbols Android+web) | Yes | Yes | Core icon implementation; fallback `@expo/material-symbols`. |
| `expo-blur` scrim | Yes (iOS). Android: wrap the app root in `BlurTargetView` and pass `blurTarget` + `blurMethod="dimezisBlurViewSdk31Plus"` to `BlurView` | Yes | Below Android 12 (API 31) fall back to a plain dimmed scrim. Never rely on blur for legibility. |
| Bottom sheets | Yes — JS sheet (Reanimated + Gesture Handler) over a blurred scrim | Yes | `@expo/ui` BottomSheet is a native modal with limited props and cannot blur the app behind it; use it only for simple sheets. |
| Local notifications (reminders, "remind me again") | Yes | Yes | Core. |
| **Remote push on Android** (FCM) | **No** (removed from Expo Go since SDK 53) | Yes — needs a development build + FCM credentials | `requires: dev-build`. In Expo Go the inbox + SSE still work; the device screen shows `Push needs the installed app` — never a fake success. |
| Remote push on iOS (APNs) | Limited; needs credentials and a registered device | Yes | Verify on a real device only; otherwise `blocked: <reason>`. |
| Passkeys (WebAuthn) | No | Yes — dev build + `associatedDomains` (iOS) / `assetlinks.json` (Android) on the real domain | `requires: dev-build`. Password + TOTP works everywhere and is the baseline. |
| Biometric lock, secure screens, document scanner, QR scanner, quick actions, deep links | Mostly yes (check each module; some config plugins need a build) | Yes | Test in Expo Go first; list any that need a build. |
| Home-screen widgets | No | Yes (config plugin / native target) | `requires: dev-build`; counts only, never amounts. |
| Custom native modules / config plugins | No | Yes | Avoid unless a requirement forces it. |

## Rules for the builder
1. `make dev` must produce a bundle that opens in Expo Go and on `http://localhost:8082` with no red screens.
2. Feature-detect at runtime (`Constants.executionEnvironment`, `Device.isDevice`, permission and module availability) and show the honest state text from the design spec (`Not configured`, `Needs the installed app`), never a silent no-op.
3. `docs/PREFLIGHT.md` lists every `requires: dev-build` item with the exact command to produce the build (`eas build --profile development --platform android|ios`) and the credentials needed (FCM service account, APNs key, Apple team, domain files).
4. Gate G-02 and G-20..G-22 are met in Expo Go only for the non-dev-build subset; the remainder is verified on a development build and recorded.

## Sources
- Expo Go limitations / dev builds: https://docs.expo.dev/develop/development-builds/introduction/
- expo-notifications (Android remote push removed from Expo Go in SDK 53): https://docs.expo.dev/versions/v58.0.0/sdk/notifications/
- expo-blur (Android BlurTargetView): https://docs.expo.dev/versions/v58.0.0/sdk/blur-view/
- @expo/ui bottom sheet: https://docs.expo.dev/versions/v58.0.0/sdk/ui/
- Passkeys with Expo: https://docs.expo.dev/versions/v58.0.0/sdk/local-authentication/ (+ platform associated-domains docs)

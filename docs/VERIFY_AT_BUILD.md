# VERIFY_AT_BUILD.md — facts that were NOT fully verified when this prompt was written

For each row: read the official source for the version you pin, record the result and date in `docs/STACK_LOCK.md`, and apply the fallback if the capability is absent. Never code against a remembered API.

| # | Item | Why it's uncertain | How to verify | Fallback |
|---|---|---|---|---|
| 1 | Expo SDK current stable, required Node, RN version | Moves quickly | docs.expo.dev SDK changelog | Pin what builds on both platforms |
| 2 | `@expo/ui` Jetpack Compose + SwiftUI component coverage and stability | Young library; coverage varies by SDK | Expo UI docs + spike S-02 | Hand-built RN components following M3/HIG metrics |
| 3 | `expo-glass-effect` props/behaviour, iOS 26 requirement, pre-26 fallback | Platform-version dependent | Expo docs + spike S-03 on device | System blur material + tokens |
| 4 | Material 3 **Expressive** availability in Compose M3 / `@expo/ui` | Page could not be fetched during research | Android Developers M3 docs for the pinned version | Standard M3 |
| 5 | `@expo/material-symbols` (or chosen Material Symbols pipeline) packaging, weights, FILL axis | Package name/API unverified | npm + repo README + spike S-07 | Bundle Material Symbols variable font or generated drawables (Apache-2.0) |
| 6 | `expo-symbols` SF Symbol names used in `DESIGN_SPEC.md §8` exist for min iOS target | Names not exhaustively checked | SF Symbols app | Pick nearest available symbol |
| 7 | Material Symbol names in §8 exist | Not exhaustively checked | fonts.google.com/icons | Nearest symbol |
| 8 | `expo-widgets` / Android widget approach | Maturity unknown | Expo docs | Config plugin + native widget, or drop M-07 with a documented exception |
| 9 | Encrypted local DB for mobile cache (SQLCipher with `expo-sqlite`) | Support unverified | Expo SQLite docs | `expo-secure-store` for keys + encrypted file blobs; or omit offline cache (M-12) with exception |
| 10 | APNs direct from backend with `aioapns` (token auth, HTTP/2) | Library status/version | PyPI + repo | `httpx[http2]` implementation or FCM-to-APNs routing via a Firebase iOS SDK |
| 11 | `getDevicePushTokenAsync` returns APNs token on iOS and FCM token on Android in the pinned `expo-notifications` | Behaviour per platform | Expo docs | Use `@react-native-firebase/messaging` for FCM tokens on both |
| 12 | iOS `time-sensitive` interruption level requirements | Entitlement/capability details | Apple docs | Use `active` level |
| 13 | DEVICE_RECEIVED signal availability (background receipt callbacks) on Android/iOS | Platform restrictions | Expo/FCM/APNs docs | Mark DEVICE_RECEIVED "not observable"; rely on OPENED/ACK |
| 14 | FCM current limits/semantics (token staleness ~1 month, expiry ~270 days, `UNREGISTERED` handling, 100 pending cap, priority behaviour) | Provider can change | Firebase docs | Follow current docs |
| 15 | Android 13+ `POST_NOTIFICATIONS` flow and channel creation order in `expo-notifications` | API details | Expo + Android docs | Native module call |
| 16 | `prefers-reduced-transparency` media-feature support; `-apple-visual-effect` | Browser support evolving | MDN / caniuse / WebKit blog | JS toggle `data-reduce-transparency` (already specified) |
| 17 | Web push on iOS (installed PWA requirement, permission gesture) | Platform policy | WebKit docs | Document limitation; inbox + SSE |
| 18 | Keycloak step-up (`acr`/`max_age`), WebAuthn passkey flows in pinned version | Version-specific config | Keycloak docs | Re-auth via `prompt=login&max_age=0` |
| 19 | `mt-940` 5.1.1 (BSD-3) and `pycamt` 1.1.1 (MIT, CAMT.053 only) versions/licences at build time | Versions move | PyPI | Alternate parser or CSV path |
| 20 | Razorpay IFSC dataset licence/terms and update cadence | Used for offline IFSC validation | Repo licence file | Flag-only validation; official RBI list import |
| 21 | pyHanko version, licence (MIT expected) and capabilities for signing receipts | Redirected docs gave little detail | pyHanko docs/repo | `pikepdf` + manual signature, or sign detached hash only |
| 22 | Every LLM provider: free-tier limits, model IDs, data-use/training terms, India availability | Change frequently; several not fetched (Mistral, NVIDIA, Brevo free e-mail limits) | Provider docs/console | Keep provider disabled |
| 23 | Gemini free-tier data use | Believed to permit product improvement use | Google AI terms | Tier-P only |
| 24 | Cerebras free-tier requirements (payment method) | Believed | Cerebras docs | Disable |
| 25 | Cloudflare Workers AI OpenAI-compatible endpoint & neuron allocation | Shape may differ | Cloudflare docs | Native REST adapter |
| 26 | Sarvam API shape/auth (not OpenAI-compatible?) | Unverified | Sarvam docs | Native adapter or disable |
| 27 | SF Symbols licence wording for any web/other use | Not retrievable | Apple SF Symbols licence | Keep SF Symbols on Apple platforms only (already specified) |
| 28 | Maestro vs Detox for RN new-architecture + Expo dev builds | Tooling choice | Their docs + spike | Whichever runs reliably in CI |
| 29 | CERT-In/DPDP/GIGW details as of go-live (staggered DPDP dates around Nov 2026 and May 2027) | Legal timelines | Gazette + counsel | Counsel-maintained matrix |
| 30 | APH 2024-27 Table 1.4 and Clause 6.46 against the final downloadable PDF + amendments | Research used indexed text; PDF endpoint did not open | Official AICTE PDF + notices | Rules stay `draft` |

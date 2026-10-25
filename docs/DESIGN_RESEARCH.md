# DESIGN_RESEARCH.md — what was measured and what was researched (24 Oct 2026)

## 1. Measurements from the reference sheet (736×1308 px, 9 phone screens)
Method: pixel sampling and zoomed crops. Dominant colours: app background ≈ `#f4f4fc` (≈50% of pixels), cards ≈ `#fcfcfc`, outer backdrop ≈ `#dce4fc`, black buttons `#181818`, soft-red pill `#fce6e8`, icon blue ≈ `#3b78d8`, "Pro" pill ≈ `#7393e8`, field grey ≈ `#ebeef7`, progress track ≈ `#e3e8fb`.
Structure observed: top bar = heavy wordmark · short black progress line + `0%` · filled bell · periwinkle pill. Hero banner = light periwinkle gradient card with sparkles, big ring, mascot peeking over the bottom edge, bold two-line greeting, round black pencil button. Lists = white cards with a small grey section label, duotone blue icons, bold titles, chevrons. Tab bar = floating white pill, four tabs, **all icons blue duotone**, active tab = soft light-blue capsule with blue bold label, inactive labels near-black bold. Buttons = black pills; destructive = soft pink pill with brick-red text; side-by-side pair for binary choices. Inputs = grey fills inside white cards, `0/120` counter. Sheet = white, top radius ≈28, grabber, mascot + one sentence + black button over a blurred dimmed backdrop. Empty state = small mascot illustration, bold line, faint sentence. Chips: selected = black pill.
Accessibility measurements of the raw reference colours: icon blue on white 4.32:1 (fine for icons, not for text); white on the "Pro" pill 2.97:1 (fails); soft-red text 3.92:1 (fails). Our tokens keep the look and fix these (primary text blue `#2d63cf` 5.53:1; role pill `#4570da` with white text ≥4.5:1; red text `#b0303f` ≥4.5:1 on the pink pill).

## 2. Platform research and decisions
| Question | Finding | Decision |
|---|---|---|
| Can Expo Router **native tabs** produce the floating white pill? | Native tabs expose `tintColor`, `indicatorColor`, `iconColor`, `labelStyle` etc., but on iOS 26+ "the system draws the tab bar" and `backgroundColor`, `blurEffect`, `shadowColor` have no effect; on Android they render Material's navigation bar. Docs do not describe a floating bar. | Use **`expo-router/ui` headless tabs** (`Tabs`, `TabSlot`, `TabList`, `TabTrigger`, `useTabTrigger`) — supported on Android, iOS and web — to build the floating pill. Native tabs stay as an optional alternative if the owner prefers the system look. |
| iOS 26 tab bars | Rebuilding with Xcode 26 gives system Liquid Glass bars that float and can minimise on scroll; on older iOS the classic bar appears. | The reference look does not use glass. Liquid Glass is an optional, default-off flag for iOS 26 only. |
| Material 3 Expressive navigation | Google replaced the tall M3 bar with a shorter "flexible" bar and supports horizontal items on medium windows; M3 indicators are already pill-shaped. | Our custom pill bar mirrors M3's capsule indicator, keeps 48 dp targets and ripples; use rail/horizontal layout on tablets/foldables. |
| Material Symbols on Android in Expo SDK 58 | `expo-symbols` (SDK 58) renders SF Symbols on iOS and **Google Material Symbols on Android and web** via `name={{ ios, android, web }}`; Android weights from `expo-symbols/androidWeights/*`. `@expo/material-symbols` ships XML drawables for `@expo/ui` `Icon` (outlined only by default). | Use `expo-symbols` as the single mobile `<Icon>` implementation (verify in spike S-02); `@expo/material-symbols` is the fallback. This replaces the earlier hook rule that banned `expo-symbols` in Android code. |
| Two-tone icon depth | SF Symbols support hierarchical rendering; Android Material Symbols have fill axis; web Phosphor has a `duotone` weight. | iOS hierarchical + azure tint; Android filled-when-selected + azure tint; web Phosphor Duotone. |
| Heading typeface | Bold geometric grotesques pair well with Inter-class body; Plus Jakarta Sans and Manrope are the common free choices. | Plus Jakarta Sans 800 (display) + Inter 500 (body), both OFL, self-hosted; Noto fallbacks for Hindi/Tamil. |
| Expo Go limits | Remote push on Android is unavailable in Expo Go (SDK 53+); passkeys and widgets need a dev build; `expo-blur` works but Android needs `BlurTargetView`; `@expo/ui` BottomSheet is a native modal with limited props. | Build for Expo Go first, mark dev-build items honestly — see `docs/EXPO_GO_VS_DEV_BUILD.md`. Bottom sheet = JS sheet over a `BlurView` scrim. |
| Safe-area/bottom padding with absolute bars | React Navigation does not pad content for absolutely positioned bars. | Provide `useFloatingTabBarHeight()` and pad every scroll view. |

## 3. Reference product
Searches for a public case study of the reference app returned no usable documentation; its design was therefore reconstructed from the image itself. Its brand assets (name, wordmark, mascot) are intentionally not reproduced.

## Sources
- Expo Go vs dev builds, expo-blur, notifications, @expo/ui: see `docs/EXPO_GO_VS_DEV_BUILD.md`
- Expo Router native tabs (SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/router/native-tabs.md
- Expo Router UI (headless tabs, SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/router/ui.md
- Expo Router tabs: https://docs.expo.dev/router/advanced/tabs.md
- expo-symbols (SDK 58): https://docs.expo.dev/versions/v58.0.0/sdk/symbols.md
- @expo/material-symbols: https://cdn.jsdelivr.net/npm/@expo/material-symbols@0.1.1/README.md
- iOS 26 tab bars with Liquid Glass: https://www.donnywals.com/exploring-tab-bars-on-ios-26-with-liquid-glass/
- Material 3 Expressive navigation: https://9to5google.com/2025/05/14/material-3-expressive-navigation/

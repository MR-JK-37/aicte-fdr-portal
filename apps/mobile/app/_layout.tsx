import { Slot } from 'expo-router';

// R0 boot shim: a bare Slot so expo-router/entry resolves and the bundle boots.
// R6 replaces this with the role-aware floating pill tab bar
// (expo-router/ui headless Tabs/TabSlot/TabList/TabTrigger per docs/DESIGN_RESEARCH.md).
//
// AuthProvider/StepUpProvider deliberately live in App.tsx, NOT here, even though
// this file wrapping <Slot/> looks like the "normal" place for them (that's how
// apps/web/src/main.tsx does it). Verified live: Metro's lazy route bundling
// (the `lazy=true` bundle param Expo Router uses) loads app/_layout.tsx and
// app/index.tsx -> ../App.tsx as separate chunks that do NOT dedupe a shared
// module — `src/auth/AuthContext.tsx` was observed executing twice (its
// top-level code ran twice, logged twice), producing two different
// `createContext()` instances, so a Provider mounted in _layout.tsx was invisible
// to `useAuth()` called in App.tsx ("must be used inside AuthProvider" at runtime
// even though the component tree looks correctly nested in source). Keeping the
// Provider and every consumer in the same bundled module sidesteps it.
export default function RootLayout() {
  return <Slot />;
}

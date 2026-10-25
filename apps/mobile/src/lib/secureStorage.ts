import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';

/**
 * Refresh-token storage. On iOS/Android this is the real Keychain/Keystore
 * (AUTH_ROLES_MATRIX.md §2.1: "rotating refresh token in Keychain / Android
 * Keystore bound to the device record"). `expo-secure-store` has no native
 * backing on web (its web module is an empty stub) — the web preview target
 * (used for local dev in this sandbox, no device/emulator available) falls
 * back to localStorage, which is NOT secure storage. This is a real,
 * documented platform limitation, not a simulated success: production
 * mobile builds (the only place this product ships end users) always use
 * the real Keychain/Keystore path.
 */
const isWeb = Platform.OS === 'web';

export async function setSecureItem(key: string, value: string): Promise<void> {
  if (isWeb) {
    localStorage.setItem(key, value);
    return;
  }
  await SecureStore.setItemAsync(key, value);
}

export async function getSecureItem(key: string): Promise<string | null> {
  if (isWeb) {
    return localStorage.getItem(key);
  }
  return SecureStore.getItemAsync(key);
}

export async function deleteSecureItem(key: string): Promise<void> {
  if (isWeb) {
    localStorage.removeItem(key);
    return;
  }
  await SecureStore.deleteItemAsync(key);
}

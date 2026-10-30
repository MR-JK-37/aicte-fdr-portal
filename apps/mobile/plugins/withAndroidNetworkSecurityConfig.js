const { withAndroidManifest, withDangerousMod } = require('expo/config-plugins');
const fs = require('fs');
const path = require('path');

/**
 * Installs a domain-scoped network_security_config.xml (localhost, the
 * Android emulator host-loopback alias, and apiClient.ts's hardcoded
 * dev-machine LAN IP) and wires it via android:networkSecurityConfig, so
 * dev/staging builds can reach the plaintext-HTTP local backend without a
 * blanket app-wide usesCleartextTraffic allowance (flagged by security
 * review — a real production backend must be HTTPS and is never covered by
 * this file). Keeps android/app/src/main/res/xml/network_security_config.xml
 * in sync across `expo prebuild` regenerations instead of relying on a
 * hand-patched native file that silently reverts.
 */
const CONFIG_XML = `<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
  <domain-config cleartextTrafficPermitted="true">
    <domain includeSubdomains="false">localhost</domain>
    <domain includeSubdomains="false">127.0.0.1</domain>
    <domain includeSubdomains="false">10.0.2.2</domain>
    <!-- apiClient.ts's hardcoded dev-machine fallback IP -->
    <domain includeSubdomains="false">192.168.31.237</domain>
  </domain-config>
</network-security-config>
`;

function withNetworkSecurityConfigFile(config) {
  return withDangerousMod(config, [
    'android',
    async (config) => {
      const xmlDir = path.join(
        config.modRequest.platformProjectRoot,
        'app/src/main/res/xml'
      );
      fs.mkdirSync(xmlDir, { recursive: true });
      fs.writeFileSync(
        path.join(xmlDir, 'network_security_config.xml'),
        CONFIG_XML
      );
      return config;
    },
  ]);
}

function withNetworkSecurityConfigManifest(config) {
  return withAndroidManifest(config, (config) => {
    const application = config.modResults.manifest.application?.[0];
    if (application) {
      application.$['android:networkSecurityConfig'] = '@xml/network_security_config';
    }
    return config;
  });
}

module.exports = function withAndroidNetworkSecurityConfig(config) {
  config = withNetworkSecurityConfigFile(config);
  config = withNetworkSecurityConfigManifest(config);
  return config;
};

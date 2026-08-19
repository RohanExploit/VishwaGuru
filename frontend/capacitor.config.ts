import type { CapacitorConfig } from '@capacitor/cli';

/**
 * Capacitor configuration for the Android build.
 *
 * `androidScheme: 'https'` keeps the WebView origin at https://localhost. That
 * origin is what the backend's CORS allowlist admits (see MOBILE_APP_ORIGINS in
 * backend/main.py), and it avoids Android's cleartext-traffic block, which
 * rejects http:// requests by default from API 28 onward.
 *
 * The app talks to the API through VITE_API_URL, baked in at build time. There
 * is no dev proxy or Netlify redirect inside the WebView, so that value must be
 * an absolute https:// URL for any device build.
 */
const config: CapacitorConfig = {
  appId: 'com.vishwaguru.app',
  appName: 'VishwaGuru',
  webDir: 'dist',
  android: {
    allowMixedContent: false,
  },
  server: {
    androidScheme: 'https',
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 1200,
      backgroundColor: '#0D1117',
      androidScaleType: 'CENTER_CROP',
      showSpinner: false,
    },
    StatusBar: {
      style: 'DARK',
      backgroundColor: '#0D1117',
    },
  },
};

export default config;

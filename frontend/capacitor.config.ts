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
    // The WebView serves the app from https://localhost, so an http:// API is
    // blocked as mixed content -- a Chromium rule, separate from Android's
    // cleartext-traffic policy, and not something the network security config
    // can waive.
    //
    // Production is unaffected: the API is served over HTTPS there, so this
    // stays false in anything shipped. It exists only so a debug build can talk
    // to an http:// dev server on the LAN, and must be opted into explicitly:
    //
    //   CAP_ALLOW_MIXED_CONTENT=true npm run mobile:sync
    allowMixedContent: process.env.CAP_ALLOW_MIXED_CONTENT === 'true',
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

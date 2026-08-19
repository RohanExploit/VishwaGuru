/**
 * Native platform bootstrap for the Capacitor build.
 *
 * Everything here is a no-op on the web, so the same bundle serves the PWA and
 * the packaged app. Inside a WebView, three things do not happen by themselves:
 *
 *  - the splash screen stays up until something dismisses it;
 *  - the status bar keeps the system default colours and overlaps the layout;
 *  - `getUserMedia` and `navigator.geolocation` fail without the Android
 *    runtime permission having been granted, and a plain web denial handler
 *    cannot request it.
 */
import { Capacitor } from '@capacitor/core';

export const isNativePlatform = () => Capacitor.isNativePlatform();

/**
 * Ask for camera access. Returns true when the app may use the camera.
 *
 * On the web this resolves true without prompting; the browser prompts when
 * getUserMedia is actually called.
 */
export async function ensureCameraPermission() {
  if (!Capacitor.isNativePlatform()) return true;

  try {
    const { Camera } = await import('@capacitor/camera');
    const status = await Camera.checkPermissions();
    if (status.camera === 'granted') return true;
    if (status.camera === 'denied') return false;

    const requested = await Camera.requestPermissions({ permissions: ['camera'] });
    return requested.camera === 'granted';
  } catch (err) {
    console.error('Camera permission request failed', err);
    return false;
  }
}

/**
 * Ask for location access. Returns true when the app may read position.
 */
export async function ensureLocationPermission() {
  if (!Capacitor.isNativePlatform()) return true;

  try {
    const { Geolocation } = await import('@capacitor/geolocation');
    const status = await Geolocation.checkPermissions();
    if (status.location === 'granted' || status.coarseLocation === 'granted') return true;

    const requested = await Geolocation.requestPermissions();
    return requested.location === 'granted' || requested.coarseLocation === 'granted';
  } catch (err) {
    console.error('Location permission request failed', err);
    return false;
  }
}

/**
 * Read the current position.
 *
 * Uses the Capacitor plugin natively, because navigator.geolocation in a
 * WebView resolves only after the Android permission is granted and gives no
 * way to request it. Falls back to the browser API on the web.
 */
export async function getCurrentPosition(options = {}) {
  const settings = { enableHighAccuracy: true, timeout: 15000, maximumAge: 0, ...options };

  if (Capacitor.isNativePlatform()) {
    const granted = await ensureLocationPermission();
    if (!granted) throw new Error('Location permission denied');

    const { Geolocation } = await import('@capacitor/geolocation');
    return Geolocation.getCurrentPosition(settings);
  }

  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by this browser'));
      return;
    }
    navigator.geolocation.getCurrentPosition(resolve, reject, settings);
  });
}

/**
 * Dismiss the splash screen and colour the status bar. Safe to call anywhere.
 */
export async function initNativeShell() {
  if (!Capacitor.isNativePlatform()) return;

  try {
    const { StatusBar, Style } = await import('@capacitor/status-bar');
    await StatusBar.setStyle({ style: Style.Dark });
    await StatusBar.setBackgroundColor({ color: '#0D1117' });
  } catch (err) {
    console.error('Status bar setup failed', err);
  }

  try {
    const { SplashScreen } = await import('@capacitor/splash-screen');
    await SplashScreen.hide();
  } catch (err) {
    console.error('Splash screen dismissal failed', err);
  }
}

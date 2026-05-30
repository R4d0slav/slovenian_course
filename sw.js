/* Slovenščina A2+/B1 — offline service worker.
 * The page populates CACHE directly (see index.html "Save for offline"),
 * so this worker only needs to (a) precache the small shell and
 * (b) serve same-origin GETs cache-first with a network fallback. */

const CACHE = 'slovenscina-course-v1';

// Small shell precached on install so the launcher/home-screen icon
// opens instantly even before the user taps "Save for offline".
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      // Don't let one missing shell file abort the whole install.
      .then((cache) => Promise.allSettled(SHELL.map((u) => cache.add(u))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return; // let CDN/font requests pass through

  // Cache-first: once "Save for offline" has run, everything is local.
  event.respondWith(
    caches.match(req).then((hit) => {
      if (hit) return hit;
      return fetch(req).then((res) => {
        if (res && res.ok && res.type === 'basic') {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
        }
        return res;
      }).catch(() => hit); // offline & uncached → undefined (browser shows its own error)
    })
  );
});

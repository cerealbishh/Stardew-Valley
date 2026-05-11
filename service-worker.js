const CACHE_NAME = 'hoedown-v4';
const ASSETS = [
  './index.html',
  './manifest.json',
  './service-worker.js',
  './update-checker.js'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS).catch((err) => {
        console.log('Some assets failed to cache (non-critical):', err);
      });
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.pathname.endsWith('.html') || url.pathname === '/') {
    e.respondWith(
      fetch(e.request)
        .then((response) => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(e.request, clone));
          return response;
        })
        .catch(() => caches.match(e.request))
    );
  } else {
    e.respondWith(
      caches.match(e.request).then((response) => response || fetch(e.request))
    );
  }
});

self.addEventListener('message', (e) => {
  if (e.data && e.data.type === 'CHECK_UPDATE') checkForUpdate();
});

async function checkForUpdate() {
  try {
    const response = await fetch('./index.html?t=' + Date.now(), { cache: 'no-store' });
    const newHtml = await response.text();
    const cached = await caches.match('./index.html');
    if (!cached) return;
    const oldHtml = await cached.text();
    if (newHtml !== oldHtml) {
      self.clients.matchAll().then((clients) => {
        clients.forEach((client) => client.postMessage({ type: 'UPDATE_AVAILABLE' }));
      });
    }
  } catch (err) {}
}

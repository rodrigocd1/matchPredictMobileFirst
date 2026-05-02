const staticCacheName = 'match-predict-static-v4';
const applicationShellFiles = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.webmanifest',
    '/icons/icon-192.png',
    '/icons/icon-512.png'
];

self.addEventListener('install', (installEvent) => {
    installEvent.waitUntil(
        caches.open(staticCacheName).then((cacheStorage) => cacheStorage.addAll(applicationShellFiles))
    );
});

self.addEventListener('activate', (activateEvent) => {
    activateEvent.waitUntil(
        caches.keys().then((cacheNames) => Promise.all(
            cacheNames
                .filter((cacheName) => cacheName !== staticCacheName)
                .map((cacheName) => caches.delete(cacheName))
        ))
    );
});

self.addEventListener('fetch', (fetchEvent) => {
    fetchEvent.respondWith(
        caches.match(fetchEvent.request).then((cachedResponse) => {
            if (cachedResponse) {
                return cachedResponse;
            }

            return fetch(fetchEvent.request);
        })
    );
});

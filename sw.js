var CACHE_NAME = 'nebula-v28';
self.addEventListener('install', function(e) { self.skipWaiting(); });
self.addEventListener('activate', function(e) { e.waitUntil(caches.keys().then(function(k) { return Promise.all(k.map(function(n) { return caches.delete(n); })); })); self.clients.claim(); });
self.addEventListener('fetch', function(e) {
    if (e.request.method !== 'GET') return;
    var url = new URL(e.request.url);
    if (url.origin !== self.location.origin) return;
    if (url.pathname.startsWith('/api/')) return;
    e.respondWith(fetch(e.request).then(function(r) {
        var c = r.clone();
        caches.open(CACHE_NAME).then(function(cache) { cache.put(e.request, c); });
        return r;
    }).catch(function() { return caches.match(e.request); }));
});
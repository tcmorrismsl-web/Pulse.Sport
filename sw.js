/* Pulse service worker: keeps the app itself on the phone so it opens instantly and offline.
   The page is network-first (so updates show right away) with the saved copy as the fallback;
   icons and the manifest are served from the cache; team lists refresh in the background.
   ESPN data is never cached here (the app keeps its own saved last update). */
const CACHE = "pulse-shell-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./icons/apple-touch-icon.png", "./icons/icon-192.png", "./icons/icon-512.png", "./icons/favicon.svg", "./icons/favicon-32.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});

function timeout(ms){ return new Promise((_, rej) => setTimeout(() => rej(new Error("timeout")), ms)); }

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;             // ESPN, fonts, YouTube TV etc. go straight to the network

  // The page: try the network briefly, fall back to the saved copy.
  if (req.mode === "navigate" || url.pathname.endsWith("/") || url.pathname.endsWith("/index.html")){
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      try {
        const res = await Promise.race([fetch(req, {cache: "no-store"}), timeout(3500)]);
        if (res && res.ok) cache.put("./index.html", res.clone());
        return res;
      } catch {
        return (await cache.match("./index.html")) || (await cache.match("./")) || Response.error();
      }
    })());
    return;
  }
  // Team lists: answer from the cache, refresh in the background.
  if (url.pathname.includes("/teams/")){
    e.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const hit = await cache.match(req);
      const net = fetch(req).then(res => { if (res.ok) cache.put(req, res.clone()); return res; }).catch(() => hit);
      return hit || net;
    })());
    return;
  }
  // Icons, manifest: cache first.
  e.respondWith(caches.match(req).then(hit => hit || fetch(req)));
});

// 부스 화면 오프라인 캐시.
// HTML 은 네트워크 우선 — 새 배포를 바로 받고, 인터넷이 끊기면 캐시로 버틴다.
// 아이콘·매니페스트는 캐시 우선. 캐시 이름은 빌드가 내용 해시로 박는다.
const C = 'booth-a111392382';
const FILES = ['./booth.html', './manifest.webmanifest', './icon-192.png', './icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(C).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  const isHtml = e.request.mode === 'navigate' || e.request.url.indexOf('.html') !== -1;
  e.respondWith(caches.match(e.request, { ignoreSearch: true }).then(hit => {
    const net = fetch(e.request).then(r => {
      if (r.ok) { const cp = r.clone(); caches.open(C).then(c => c.put(e.request, cp)); }
      return r;
    }).catch(function(){ return hit; });
    return isHtml ? net : (hit || net);
  }));
});

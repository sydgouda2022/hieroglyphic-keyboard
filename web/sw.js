/* Standalone app shell and dictionary offline cache. No external app URLs required. */
const VERSION='hieroglyphic-keyboard-v1';
const CORE=['./','./index.html','./styles.css','./app.mjs','./editor-core.mjs','./keyboard_search.mjs','./_generic_search.mjs','./lexicon_install.mjs','./manifest.webmanifest','./icon.svg','./signs.json','./font.ttf'];
const PREFIX='hieroglyphic-keyboard-';
self.addEventListener('install',e=>e.waitUntil((async()=>{
 const cache=await caches.open(VERSION);
 await cache.addAll(CORE);
 await self.skipWaiting();
})()));
self.addEventListener('activate',e=>e.waitUntil((async()=>{
 const names=await caches.keys();
 await Promise.all(names.filter(x=>x.startsWith(PREFIX)&&x!==VERSION).map(x=>caches.delete(x)));
 await self.clients.claim();
})()));
self.addEventListener('fetch',e=>{
 if(e.request.method!=='GET')return;
 const url=new URL(e.request.url);
 if(url.origin!==self.location.origin)return;
 e.respondWith((async()=>{
  const cache=await caches.open(VERSION);
  const found=await cache.match(e.request,{ignoreSearch:true});
  if(found)return found;
  try{
   const response=await fetch(e.request);
   if(response.ok) e.waitUntil(cache.put(e.request,response.clone()).catch(()=>{}));
   return response;
  }catch{
   if(e.request.mode==='navigate')return await cache.match('./index.html')||Response.error();
   return new Response('Offline asset unavailable',{status:503});
  }
 })());
});

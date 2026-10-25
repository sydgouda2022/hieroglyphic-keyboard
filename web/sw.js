/* Optional standalone app's service worker. Library integrations do NOT import this. */
const VERSION='hieroglyphic-keyboard-v1';
const CORE=['./','./index.html','./styles.css','./app.mjs','./editor-core.mjs',
 './keyboard_api.mjs','./keyboard_ui.mjs','./keyboard_catalog.js',
 './keyboard_search.mjs','./_generic_search.mjs','./lexicon_install.mjs',
 './manifest.webmanifest','./icon.svg','./signs.json','./font.ttf',
 './lexicon/manifest.json','./lexicon/lexicon.json'];
const PREFIX='hieroglyphic-keyboard-';
self.addEventListener('install',event=>event.waitUntil((async()=>{
 const cache=await caches.open(VERSION);
 await cache.addAll(CORE);
 await self.skipWaiting();
})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{
 const names=await caches.keys();
 await Promise.all(names.filter(x=>x.startsWith(PREFIX)&&x!==VERSION).map(x=>caches.delete(x)));
 await self.clients.claim();
})()));
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url);
 if(url.origin!==self.location.origin)return;
 event.respondWith((async()=>{
  const cache=await caches.open(VERSION);
  const cached=await cache.match(event.request,{ignoreSearch:true});
  const lexicon=url.pathname.endsWith('/lexicon/manifest.json')||url.pathname.endsWith('/lexicon/lexicon.json');
  if(cached&&!lexicon)return cached;
  try{
   const response=await fetch(event.request,lexicon?{cache:'no-store'}:undefined);
   if(response.ok)event.waitUntil(cache.put(event.request,response.clone()).catch(()=>{}));
   return response;
  }catch{
   if(cached)return cached;
   if(event.request.mode==='navigate')return await cache.match('./index.html')||Response.error();
   return new Response('Offline asset unavailable',{status:503});
  }
 })());
});

// Service worker: que la ruta siga andando cuando se cae la señal en el sitio.
//
// Se registra como sw.js?v=N con la V de catalogo.js, así que cada versión nueva del
// sitio es un service worker nuevo con su propio caché, y el viejo se borra entero.
//
// Tres maneras de responder:
//  - páginas y JSON de datos: primero la red, porque cambian seguido; si no contesta
//    a tiempo, lo guardado.
//  - todo lo demás (código, fuentes, fotos, modelos): primero lo guardado, que para
//    esta versión no cambia.
//  - analitica/, impresos, PDF y modelos de escritorio: ni se tocan. Son pesados o no
//    tienen sentido sin red.

const V = new URL(location.href).searchParams.get('v') || '0';
const CACHE = `mv-${V}`;
const RAIZ = new URL('./', location.href).href;

// Lo mínimo para abrir cualquier página sin red. Se baja al instalar.
const ESQUELETO = [
  'index.html', 'catalogo.html', 'pieza.html', 'visor.html', 'panorama.html', 'ar.html', '404.html',
  'libro.html',
  'assets/css/app.css', 'assets/css/ar.css', 'assets/css/visor.css',
  'assets/js/catalogo.js', 'assets/js/navegacion.js', 'assets/js/sensor.js',
  'assets/js/analitica.js', 'assets/js/offline.js',
  'assets/js/ar/escena.js', 'assets/js/ar/piezas.js', 'assets/js/ar/ajuste.js',
  'assets/js/ar/deteccion.js', 'assets/js/ar/seguimiento.js', 'assets/js/ar/gestos.js',
  'assets/js/ar/saltos.js', 'assets/js/ar/camara.js',
  'assets/js/nube.js', 'assets/js/foto.js',
  'assets/js/visor/materiales.js', 'assets/js/visor/contorno.js',
  'assets/js/visor/vista.js', 'assets/js/visor/luz.js', 'assets/js/visor/detalle.js',
  'assets/js/visor/hoja.js', 'assets/js/visor/elegir.js', 'assets/js/visor/molde.js',
  'assets/fonts/fraunces-latin.woff2', 'assets/fonts/fraunces-latin-ext.woff2',
  'assets/fonts/plus-jakarta-sans-latin.woff2', 'assets/fonts/plus-jakarta-sans-latin-ext.woff2',
  'assets/marca/icono.svg', 'assets/marca/logo-uach-blanco.webp',
  'assets/marca/equipo/debaq.webp', 'assets/marca/equipo/vanne11.webp',
  'assets/marca/equipo/fernandandreatm.webp', 'assets/marca/equipo/pukem.webp',
  'assets/data/catalogo.json', 'assets/data/marcadores.json',
  'assets/data/banderitas.json', 'assets/data/catalogo-paginas.json',
  'assets/vendor/three/three.module.js', 'assets/vendor/three/three.core.js',
  'assets/vendor/three/addons/loaders/GLTFLoader.js',
  'assets/vendor/three/addons/loaders/DRACOLoader.js',
  'assets/vendor/three/addons/utils/BufferGeometryUtils.js',
  'assets/vendor/three/addons/environments/RoomEnvironment.js',
  'assets/vendor/three/addons/libs/draco/draco_wasm_wrapper.js',
  'assets/vendor/three/addons/libs/draco/draco_decoder.wasm',
  'assets/vendor/model-viewer/model-viewer.min.js',
  'assets/vendor/js-aruco2/cv.js', 'assets/vendor/js-aruco2/aruco.js',
  'assets/vendor/js-aruco2/dictionaries/aruco_4x4_1000.js',
  'assets/vendor/js-aruco2/svd.js', 'assets/vendor/js-aruco2/posit1.js',
  'assets/pano/sitio-360-2k.webp', 'assets/pano/sitio-360-4k.webp', 'assets/pano/parche-real.webp',
];

// Lo que no se guarda nunca, ni siquiera de pasada. De los modelos, sólo quedan fuera
// los de escritorio de cada pieza (LCDCP-…, varios MB): el molde de la huella sí va.
const NO_TOCAR = /\/analitica\/|\/assets\/impresos\/|\.pdf$|\/assets\/models\/LCDCP-[^/]+\.glb$/;
const DATOS = /\/assets\/data\/[^/]+\.json$/;
const ESPERA_RED = 3500;          // en el sitio la señal a veces "conecta" y no trae nada

// ---------- claves
// La misma foto se pide con ?v=N desde una página y sin él desde otra: se guarda una
// sola vez, sin el número. Las páginas se guardan sin su ?id=, que sólo lee el JS.
function clave(url, esPagina) {
  const u = new URL(url);
  if (esPagina) {
    u.search = '';
    if (u.href === RAIZ) u.href = RAIZ + 'index.html';
  }
  u.searchParams.delete('v');
  u.hash = '';
  return u.href;
}

async function guardar(url, respuesta) {
  if (!respuesta || respuesta.status !== 200 || respuesta.type !== 'basic') return;
  // una respuesta que vino de una redirección no se puede entregar a una navegación:
  // el navegador la rechaza. Se guarda una copia limpia.
  if (respuesta.redirected)
    respuesta = new Response(respuesta.body, { status: 200, headers: respuesta.headers });
  const cache = await caches.open(CACHE);
  await cache.put(url, respuesta);
}

// ---------- instalar y activar
self.addEventListener('install', event => {
  event.waitUntil((async () => {
    // de a uno: si falta un archivo, el resto igual se guarda
    await Promise.allSettled(ESQUELETO.map(async p => {
      await guardar(clave(RAIZ + p, p.endsWith('.html')), await fetch(RAIZ + p, { cache: 'no-cache' }));
    }));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    for (const nombre of await caches.keys())
      if (nombre.startsWith('mv-') && nombre !== CACHE) await caches.delete(nombre);
    await self.clients.claim();
  })());
});

// ---------- llenar: fotos y modelos de todas las piezas
// Lo pide la página una vez cargada (assets/js/offline.js), no la instalación: son
// ~9 MB y mientras la instalación no termina no hay nada disponible sin red. Se puede
// cortar y retomar: lo que ya está guardado no se vuelve a bajar.
self.addEventListener('message', event => {
  if (event.data?.tipo === 'llenar') event.waitUntil(llenar(event.data.modelos !== false));
});

async function llenar(conModelos) {
  const cache = await caches.open(CACHE);
  let cat;
  try {
    const r = await cache.match(RAIZ + 'assets/data/catalogo.json') || await fetch(RAIZ + 'assets/data/catalogo.json');
    cat = await r.clone().json();
  } catch { return; }

  const lista = [];
  for (const p of cat.piezas) {
    if (p.media?.imagen_movil) lista.push(p.media.imagen_movil);
    if (conModelos && p.media?.modelo_movil) lista.push(p.media.modelo_movil);
    if (p.contorno) lista.push(p.contorno);
    if (p.molde) lista.push(p.molde);
  }
  try {
    const pags = await (await cache.match(RAIZ + 'assets/data/catalogo-paginas.json'))?.json();
    for (const n of pags?.paginas || []) lista.push(`assets/catalogo/thumbs/p-${String(n).padStart(2, '0')}.webp`);
  } catch { /* sin miniaturas del catálogo, no pasa nada */ }

  // de a dos: con mala señal, pedir todo junto hace que nada termine
  const pendientes = [];
  for (const p of lista) {
    const k = clave(RAIZ + p, false);
    if (!await cache.match(k)) pendientes.push(k);
  }
  // Se pide con la versión aunque se guarde sin ella: el servidor cachea un año los medios,
  // y sin el número el navegador podría entregar la copia vieja de un archivo que cambió.
  const conVersion = k => `${k}${k.includes('?') ? '&' : '?'}v=${V}`;
  const trabajar = async () => {
    while (pendientes.length) {
      const k = pendientes.shift();
      try { await guardar(k, await fetch(conVersion(k))); } catch { /* sin red: se retoma en la próxima visita */ }
    }
  };
  await Promise.all([trabajar(), trabajar()]);
}

// ---------- responder
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || req.headers.has('range')) return;
  const url = new URL(req.url);
  if (url.origin !== location.origin || !req.url.startsWith(RAIZ) || NO_TOCAR.test(url.pathname)) return;

  const esPagina = req.mode === 'navigate';
  if (esPagina || DATOS.test(url.pathname)) {
    event.respondWith(primeroRed(req, clave(req.url, esPagina), event));
    return;
  }

  // Un pedido con otra versión viene de una página más nueva que este service worker:
  // se va a la red, y lo guardado queda para esta versión.
  const v = url.searchParams.get('v');
  if (v && v !== V) {
    event.respondWith(fetch(req).catch(() => caches.match(clave(req.url, false))));
    return;
  }
  event.respondWith(primeroGuardado(req, clave(req.url, false), event));
});

async function primeroRed(req, k, event) {
  const red = fetch(req).then(r => {
    if (r.ok) event.waitUntil(guardar(k, r.clone()));
    return r;
  });
  red.catch(() => {});             // si gana el reloj y después la red falla, que no ensucie la consola
  const tarde = new Promise(ok => setTimeout(ok, ESPERA_RED, null));
  try {
    const r = await Promise.race([red, tarde]);
    if (r) return r;
  } catch { /* sin red */ }

  const guardado = await caches.match(k);
  if (guardado) return guardado;
  // nada guardado: esperar lo que traiga la red; si tampoco, la portada
  try { return await red; }
  catch {
    return (req.mode === 'navigate' && await caches.match(RAIZ + 'index.html'))
      || new Response('Sin conexión', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
  }
}

async function primeroGuardado(req, k, event) {
  const guardado = await caches.match(k);
  if (guardado) return guardado;
  const r = await fetch(req);
  event.waitUntil(guardar(k, r.clone()));
  return r;
}

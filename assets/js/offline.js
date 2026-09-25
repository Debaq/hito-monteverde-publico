// Registra el service worker (sw.js) para que la ruta funcione sin señal.
//
// Una vez cargada la página le pide que baje las fotos y los modelos de todas las
// piezas, así la visita sigue aunque la red se caiga a mitad de camino. Con ahorro de
// datos activado sólo se bajan las fotos.

// La versión viene en la URL con que la página importa este módulo (?v=N), que es la
// que mantiene tools/version.py. Importar catalogo.js para leer V fijaría el número aquí.
const V = new URL(import.meta.url).searchParams.get('v') || '0';

// En local se está editando: un caché de por medio sirve archivos viejos y confunde.
// Para probarlo igual: localStorage.setItem('mv:offline', '1') y recargar.
const LOCAL = /^(localhost|127\.|192\.168\.|10\.)/.test(location.hostname);
const probar = (() => { try { return localStorage.getItem('mv:offline') === '1'; } catch { return false; } })();

if ('serviceWorker' in navigator) {
  if (LOCAL && !probar) {
    // si quedó uno de una prueba anterior, fuera
    navigator.serviceWorker.getRegistrations()
      .then(rs => rs.forEach(r => r.unregister())).catch(() => {});
  } else {
    const raiz = new URL('../../', import.meta.url);
    navigator.serviceWorker.register(new URL(`sw.js?v=${V}`, raiz), { scope: raiz.pathname })
      .then(() => navigator.serviceWorker.ready)
      .then(reg => {
        const pedir = () => reg.active?.postMessage({
          tipo: 'llenar',
          modelos: !navigator.connection?.saveData,
        });
        // después de la carga, para no competir con lo que la página necesita ya
        if (document.readyState === 'complete') setTimeout(pedir, 2000);
        else addEventListener('load', () => setTimeout(pedir, 2000), { once: true });
      })
      .catch(() => { /* sin service worker el sitio funciona igual, con red */ });
  }
}

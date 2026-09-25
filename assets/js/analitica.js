// Cuenta visitas en nuestro propio servidor (analitica/registrar.php).
//
// Sin cookies ni nada guardado en el teléfono: el servidor reconoce a la misma
// persona sólo dentro del día. Importar este módulo ya anota la vista de la página.

const REGISTRO = new URL('../../analitica/registrar.php', import.meta.url).href;

// En local no hay PHP detrás y las pruebas ensuciarían los números.
const ACTIVA = location.protocol === 'https:' &&
  !/^(localhost|127\.|192\.168\.|10\.)/.test(location.hostname);

const PARAMS = new URLSearchParams(location.search);
const PAGINA = location.pathname.split('/').pop() || 'index.html';

export function registrar(evento, datos = {}) {
  if (!ACTIVA) return;
  const cuerpo = JSON.stringify({ evento, pagina: PAGINA, ...datos });
  try {
    if (!navigator.sendBeacon?.(REGISTRO, cuerpo))
      fetch(REGISTRO, { method: 'POST', body: cuerpo, keepalive: true }).catch(() => {});
  } catch { /* contar nunca puede romper la página */ }
}

// Cómo llegó a esta página. "directa" es sin página anterior: un QR escaneado, un
// enlace escrito o guardado. Es lo más cerca que se puede estar de contar escaneos
// sin cambiar los carteles ya impresos.
function entrada() {
  if (PARAMS.get('volver') === 'ar') return 'ar';
  if (!document.referrer) return 'directa';
  try {
    const r = new URL(document.referrer);
    return r.origin === location.origin ? 'interna' : r.hostname;
  } catch { return 'directa'; }
}

registrar('vista', { pieza: PARAMS.get('id') || '', entrada: entrada() });

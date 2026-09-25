// Volver atrás, igual en todas las páginas.
//
// Se usa la historia del navegador, que ya recuerda la posición del scroll y la página
// del catálogo. Pero aquí la mitad de las visitas entra directo desde un QR y no tiene
// historia previa: para esos casos cada página declara a dónde volver.

const MISMO_SITIO = () => {
  try { return document.referrer && new URL(document.referrer).origin === location.origin; }
  catch { return false; }
};

export function volverAtras(destino = 'index.html') {
  if (history.length > 1 && MISMO_SITIO()) history.back();
  else location.href = destino;
}

/** Botón de volver en la barra superior. `destino` es el respaldo sin historia. */
export function montarVolver(destino = 'index.html', etiqueta = 'Volver') {
  const barra = document.querySelector('.topbar');
  if (!barra) return;
  const b = document.createElement('button');
  b.className = 'chip ghost volver';
  b.type = 'button';
  b.innerHTML = `<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor"
                   stroke-width="2.2"><path d="M15 5l-7 7 7 7"/></svg>${etiqueta}`;
  b.addEventListener('click', () => volverAtras(destino));
  barra.insertBefore(b, barra.firstChild);
  return b;
}

/** Recuerda la última pieza vista, para poder ofrecer "volver a la pieza" desde otras páginas. */
export function recordarPieza(codigo) {
  try { sessionStorage.setItem('mv:pieza', codigo); } catch { /* modo privado */ }
}

export function ultimaPieza() {
  try { return sessionStorage.getItem('mv:pieza'); } catch { return null; }
}

/** Destino de vuelta declarado en la URL (?desde=CODIGO), o la última pieza vista. */
export function origen() {
  const desde = new URLSearchParams(location.search).get('desde') || ultimaPieza();
  return desde ? { codigo: desde, url: `pieza.html?id=${encodeURIComponent(desde)}` } : null;
}

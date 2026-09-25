// Acceso al catálogo. Una sola carga, cacheada, para todas las páginas.

const RUTA = new URL('../data/catalogo.json', import.meta.url);

let cache = null;

export async function cargarCatalogo() {
  if (!cache) {
    const r = await fetch(RUTA, { cache: 'no-cache' });   // revalida: el catálogo cambia seguido
    if (!r.ok) throw new Error(`no se pudo leer el catálogo (${r.status})`);
    cache = await r.json();
  }
  return cache;
}

export async function pieza(codigo) {
  const cat = await cargarCatalogo();
  return cat.piezas.find(p => p.codigo === codigo) || null;
}

export async function vecinas(codigo) {
  const cat = await cargarCatalogo();
  const i = cat.piezas.findIndex(p => p.codigo === codigo);
  if (i < 0) return { anterior: null, siguiente: null, indice: -1, total: cat.piezas.length };
  return {
    anterior: i > 0 ? cat.piezas[i - 1] : cat.piezas[cat.piezas.length - 1],
    siguiente: i < cat.piezas.length - 1 ? cat.piezas[i + 1] : cat.piezas[0],
    indice: i,
    total: cat.piezas.length,
  };
}

// versión de los medios: subirla obliga al navegador a bajar de nuevo modelos e imágenes
export const V = 41;

// las rutas del catálogo ya vienen relativas a la raíz, donde viven las páginas
export const ruta = p => (p ? `${p}?v=${V}` : null);

export const tieneModelo = p => Boolean(p?.media?.modelo);

// acá se escribe 9,9 y no 9.9: el punto decimal del JSON es del archivo, no del idioma
export const numero = v => typeof v === 'number' ? v.toLocaleString('es-CL') : v;

export function dimsTexto(p) {
  const d = p.dimensiones || {};
  const partes = [d.largo, d.ancho, d.espesor].filter(v => v != null);
  return partes.length ? `${partes.map(numero).join(' × ')} ${d.unidad || 'cm'}`
                       : (p.dimensiones_texto || '—');
}

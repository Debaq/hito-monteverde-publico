// Guarda lo que se está viendo como imagen, con el nombre de la pieza abajo.
//
// La usan el visor 3D y la cámara AR. En el teléfono abre el menú de compartir, que es
// desde donde se guarda en la galería o se manda; en el computador la descarga.
//
// Quien llama arma el cuadro: un lienzo con la escena recién dibujada. Tiene que ser
// recién dibujada porque WebGL borra lo que mostró apenas llega a la pantalla, y un
// lienzo leído después sale en negro.

const FONDO = '#16110C', CREMA = '#EDE3D2', ARENA = '#B9A88F', OCRE = '#D08303';

/**
 * `cuadro`: el lienzo a guardar. `pieza`: la ficha, para el pie y el nombre del archivo.
 * `que`: si la foto no es de la pieza misma, qué es (el molde), para el pie y el archivo.
 * Devuelve cómo salió ('compartir' o 'descargar'), o null si la persona desistió.
 */
export async function sacarFoto(cuadro, pieza, que = '') {
  const w = cuadro.width, h = cuadro.height;
  const pie = Math.round(Math.max(84, Math.min(w, h) * .16));
  const lienzo = document.createElement('canvas');
  lienzo.width = w;
  lienzo.height = h + pie;
  const ctx = lienzo.getContext('2d');
  ctx.drawImage(cuadro, 0, 0);                     // antes de cualquier espera: el cuadro es de ahora

  // pie en dos líneas, para que el nombre quepa entero también en un teléfono angosto
  ctx.fillStyle = FONDO;
  ctx.fillRect(0, h, w, pie);
  ctx.fillStyle = OCRE;
  ctx.fillRect(0, h, w, Math.max(2, pie * .035));
  if (document.fonts?.status !== 'loaded') await document.fonts?.ready;   // las del sitio
  const margen = pie * .3;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'alphabetic';
  ctx.fillStyle = CREMA;
  ctx.font = `600 ${Math.round(pie * .3)}px Fraunces, Georgia, serif`;
  const titulo = que ? `${pieza.denominacion} — ${que}` : pieza.denominacion;
  ctx.fillText(recortar(ctx, titulo, w - 2 * margen), margen, h + pie * .5);
  ctx.fillStyle = ARENA;
  ctx.font = `500 ${Math.round(pie * .17)}px 'Plus Jakarta Sans', system-ui, sans-serif`;
  ctx.fillText(recortar(ctx, `Hito Monte Verde · ${pieza.codigo}`, w - 2 * margen), margen, h + pie * .79);

  const blob = await new Promise(ok => lienzo.toBlob(ok, 'image/jpeg', .9));
  const archivo = `monte-verde-${pieza.codigo}${que ? '-' + que.replace(/^el /, '') : ''}.jpg`;

  // En el teléfono, compartir: desde ahí se guarda en la galería. En el computador el
  // menú de compartir estorba más de lo que ayuda: se descarga y listo.
  const telefono = matchMedia('(pointer: coarse)').matches;
  const file = new File([blob], archivo, { type: 'image/jpeg' });
  if (telefono && navigator.canShare?.({ files: [file] })) {
    try {
      await navigator.share({ files: [file], title: `${titulo} — Monte Verde` });
      return 'compartir';
    } catch (e) {
      if (e.name === 'AbortError') return null;    // cerró el menú: no es un error
      // cualquier otro fallo del menú, a descargar
    }
  }
  const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: archivo });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  return 'descargar';
}

// un nombre largo no se monta sobre la firma: se corta con puntos suspensivos
function recortar(ctx, texto, ancho) {
  if (ctx.measureText(texto).width <= ancho) return texto;
  while (texto.length > 1 && ctx.measureText(texto + '…').width > ancho) texto = texto.slice(0, -1);
  return texto.trimEnd() + '…';
}

// Atajos a otras páginas de la ruta desde la cámara: el visitante apunta al cartel del
// 360 y se le ofrece abrirlo, sin salir a la cámara del teléfono.
//
// Dos caminos: el marcador ArUco del cartel (anda en cualquier teléfono, lo ve el mismo
// detector de piezas) y el QR (sólo donde hay BarcodeDetector, que trae Chrome en
// Android; donde no exista, simplemente no pasa nada).

const $ = id => document.getElementById(id);

const DESTINOS = {
  'panorama.html': 'Sitio 360°',
  'catalogo.html': 'Catálogo de la colección',
  'index.html': 'Inicio de la ruta',
};

// Sólo el detector nativo. Se probó jsQR como respaldo para iPhone y se descartó: sobre
// el cuadro de la cámara tardaba decenas de segundos por lectura, y esto corre dentro
// del mismo bucle que ya hace la detección de marcadores.
const nativoQR = ('BarcodeDetector' in window)
  ? new BarcodeDetector({ formats: ['qr_code'] }) : null;

/** `cuadro`: el lienzo con el último cuadro analizado. */
export function montarSaltos(cuadro) {
  let tQR = 0, leyendo = false, descartado = '';

  function ofrecer(url, titulo) {
    if (descartado === url || $('salto').classList.contains('on')) return;
    $('saltoTitulo').textContent = titulo;
    $('saltoSi').href = url;
    $('salto').classList.add('on');
  }

  // al 360 se entra sabiendo de dónde: así puede ofrecer la vuelta a la cámara
  const conVuelta = u => u.pathname.endsWith('panorama.html') ? `${u.href}${u.search ? '&' : '?'}volver=ar` : u.href;

  $('saltoNo').addEventListener('click', () => {
    descartado = $('saltoSi').href;                         // no volver a insistir con ese
    $('salto').classList.remove('on');
  });

  return {
    /** Un marcador de atajo a la vista: `destino` es la página, como en marcadores.json. */
    marcador(destino) {
      const u = new URL(destino, location.href);
      ofrecer(`${u.href}${u.search ? '&' : '?'}volver=ar`, DESTINOS[destino] || destino);
    },

    /** Busca QR de la propia ruta en el cuadro. Dos lecturas por segundo bastan. */
    async mirarQR(ahora) {
      if (!nativoQR || leyendo || ahora - tQR < 700) return;
      tQR = ahora;
      leyendo = true;
      try {
        for (const c of await nativoQR.detect(cuadro)) {
          let u;
          try { u = new URL(c.rawValue, location.href); } catch { continue; }
          if (u.origin !== location.origin) continue;          // sólo códigos de la propia ruta
          const titulo = DESTINOS[u.pathname.split('/').pop() || 'index.html'];
          if (titulo) ofrecer(conVuelta(u), titulo);
        }
      } catch { /* la cámara aún no da un cuadro utilizable */ }
      leyendo = false;
    },
  };
}

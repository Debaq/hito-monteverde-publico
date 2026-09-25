// Detección de marcadores ArUco en el video y pose de la pieza respecto de la cámara.
//
// Usa js-aruco2 (AR y POS), que ar.html carga como scripts clásicos antes que esto.

const CAMPO_H = 62;                // campo horizontal típico de una cámara trasera, en grados
const ANCHO_ANALISIS = 640;        // más píxeles = esquinas más precisas, y más trabajo

/**
 * `porId`: id de marcador -> { codigo, tipo, lado_mm }. El lado no es decorativo: la
 * pose sale de comparar el marcador visto con su tamaño real, así que un número
 * equivocado deja la pieza a la distancia equivocada.
 */
export function crearDetector({ video, camara, porId }) {
  const detector = new AR.Detector({ dictionaryName: 'ARUCO_4X4_1000' });
  const trabajo = document.createElement('canvas');
  const tctx = trabajo.getContext('2d', { willReadFrequently: true });
  let posit = null, ladoPosit = 0;
  let focal = 0;                   // en píxeles del cuadro de análisis

  /**
   * Alinea la cámara 3D con lo que se está viendo del video.
   *
   * El video se muestra con object-fit: cover, así que la pantalla no muestra el cuadro
   * entero sino un recorte centrado. Antes el campo de la cámara 3D se calculaba sobre el
   * cuadro completo: en teléfono vertical, con un video 16:9 recortado a 9:19.5, sobraba
   * más de la mitad del ancho y la pieza caía lejos del marcador.
   */
  function alinearCamara() {
    const vw = video.videoWidth, vh = video.videoHeight;
    if (!vw || !vh || !trabajo.width) return;      // todavía no hay cuadro que medir
    focal = (trabajo.width / 2) / Math.tan(CAMPO_H * Math.PI / 360);

    // cuánto del video entra en pantalla, en píxeles del cuadro de análisis
    const escala = Math.max(innerWidth / vw, innerHeight / vh);       // lo que hace cover
    const altoVisible = (innerHeight / escala) * (trabajo.height / vh);

    camara.fov = 2 * Math.atan((altoVisible / 2) / focal) * 180 / Math.PI;
    camara.aspect = innerWidth / innerHeight;
    camara.updateProjectionMatrix();
  }

  function pose(marcador, ladoMm) {
    const w = trabajo.width, h = trabajo.height;
    if (!focal) alinearCamara();
    if (!posit || ladoPosit !== ladoMm) { posit = new POS.Posit(ladoMm, focal); ladoPosit = ladoMm; }
    const esquinas = marcador.corners.map(c => ({ x: c.x - w / 2, y: h / 2 - c.y }));
    return posit.pose(esquinas);
  }

  return {
    trabajo,                       // el último cuadro analizado: lo reusa la lectura de QR
    alinearCamara,
    /** Cámara nueva, campo nuevo. */
    olvidarCamara() { focal = 0; alinearCamara(); },

    /** Ajusta el cuadro de análisis a la proporción del video. false si no hay video. */
    preparar() {
      if (video.readyState !== video.HAVE_ENOUGH_DATA) return false;
      const w = ANCHO_ANALISIS, h = Math.round(w * video.videoHeight / video.videoWidth);
      if (trabajo.width !== w || trabajo.height !== h) {
        trabajo.width = w; trabajo.height = h;
        posit = null; alinearCamara();          // cambió el cuadro: focal y campo se rehacen
      }
      return true;
    },

    /**
     * Lee el cuadro actual. `ids` son todos los marcadores vistos; `mejor`, el de pieza
     * más grande en pantalla, que es el mejor definido, con su pose en la escena.
     */
    leer() {
      const w = trabajo.width, h = trabajo.height;
      tctx.drawImage(video, 0, 0, w, h);
      let marcas = [];
      try { marcas = detector.detect(tctx.getImageData(0, 0, w, h)); } catch { marcas = []; }

      let mejor = null, area = 0;
      for (const m of marcas) {
        const info = porId.get(m.id);
        if (!info) continue;
        const c = m.corners;
        const a = Math.abs((c[0].x - c[2].x) * (c[1].y - c[3].y) - (c[1].x - c[3].x) * (c[0].y - c[2].y)) / 2;
        if (a > area) { area = a; mejor = { m, info }; }
      }
      const ids = marcas.map(m => m.id);
      if (!mejor) return { ids, mejor: null };

      const p = pose(mejor.m, mejor.info.lado_mm);
      const R = p.bestRotation, T = p.bestTranslation;
      const rx = -Math.asin(-R[1][2]);
      const ry = -Math.atan2(R[0][2], R[2][2]);
      const rz = Math.atan2(R[1][0], R[1][1]);
      return {
        ids,
        mejor: {
          codigo: mejor.info.codigo,
          objetivo: { x: T[0], y: T[1], z: -T[2], rx, ry, rz },
          // la misma pose en números, para el HUD de ?debug=1
          lectura: { id: mejor.m.id, tipo: mejor.info.tipo,
                     dist: Math.hypot(T[0], T[1], T[2]), lado: Math.sqrt(area),
                     rx: rx * 180 / Math.PI, ry: ry * 180 / Math.PI, rz: rz * 180 / Math.PI },
        },
      };
    },
  };
}

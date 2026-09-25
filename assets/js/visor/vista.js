// Cómo se mira la pieza: un dedo la gira, dos acercan, y los botones de zoom y encuadre.
//
// Dos maneras de girar, según la ficha (`camara` del catálogo):
//  - libre: la cámara queda quieta y gira la pieza, como en la mano bajo una luz fija.
//  - acotada (la huella): la cámara orbita dentro de unos topes para no perder la cara.
import * as THREE from 'three';

const $ = id => document.getElementById(id);

export function montarVista({ canvas, camara, pieza, tam, cam, pedir }) {
  let radioBase = tam.length() * (cam.distancia ?? 1.45);
  const LIBRE = cam.libre === true;
  const TOPE_X = (cam.giro ?? 46) * Math.PI / 180;
  // misma convención que la ficha: phi es el ángulo desde arriba
  const centroY = (90 - (cam.phi ?? 30)) * Math.PI / 180;
  const rangoY = (cam.rango ?? 28) * Math.PI / 180;
  const TOPE_Y = [centroY - rangoY, centroY + rangoY];
  let gx = 0, gy = centroY;
  // el zoom mueve la cámara, no el campo: así la perspectiva no se deforma al acercar
  let acercamiento = cam.zoom ?? 1;

  const vista = {
    alAjustar: null,                 // lo define el panel de ?debug=1, si está
    get acercamiento() { return acercamiento; },
    set acercamiento(v) { acercamiento = v; },
    radio: () => radioBase,
    /** Distancia base, como factor del tamaño de la pieza. */
    fijarDistancia(k) { radioBase = tam.length() * k; },

    ubicar() {
      pedir();
      if (LIBRE) {                   // la cámara no se mueve: lo que gira es la pieza
        camara.position.set(0, 0, radioBase / (acercamiento || 1));
        camara.lookAt(0, 0, 0);
        return;
      }
      const R = radioBase;
      camara.position.set(R * Math.cos(gy) * Math.sin(gx), R * Math.sin(gy),
                          R * Math.cos(gy) * Math.cos(gx));
      camara.position.setLength(radioBase / (acercamiento || 1));
      camara.lookAt(0, 0, 0);
    },

    aplicarZoom() {
      pedir();
      acercamiento = Math.max(.5, Math.min(6, acercamiento));
      camara.position.setLength(radioBase / acercamiento);
      vista.alAjustar?.();
    },

    encuadre() {
      acercamiento = cam.zoom ?? 1;
      gx = 0; gy = centroY;
      if (LIBRE) pieza.quaternion.identity();
      vista.ubicar(); vista.aplicarZoom();
    },
  };

  // Giro libre por cuaterniones, no por ángulos: con coordenadas esféricas siempre queda
  // un tope cerca de los polos y la pieza no se puede dar vuelta del todo. Aquí se acumula
  // la rotación sobre la pieza, como girarla en la mano bajo una luz fija.
  const girarPieza = (dx, dy) => {
    pedir();
    const q = new THREE.Quaternion();
    q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), -dx * .008);
    pieza.quaternion.premultiply(q);
    q.setFromAxisAngle(new THREE.Vector3(1, 0, 0), -dy * .008);
    pieza.quaternion.premultiply(q);
  };

  // ---------- un dedo gira la pieza; dos dedos acercan
  const dedos = new Map();
  let arrastre = null, pellizco = null;
  const separacion = () => {
    const [a, b] = [...dedos.values()];
    return Math.hypot(a.x - b.x, a.y - b.y);
  };

  canvas.addEventListener('pointerdown', e => {
    dedos.set(e.pointerId, { x: e.clientX, y: e.clientY });
    canvas.setPointerCapture(e.pointerId);
    if (dedos.size === 2) { pellizco = separacion(); arrastre = null; }
    else arrastre = [e.clientX, e.clientY];
  });
  const soltar = e => {
    dedos.delete(e.pointerId);
    if (dedos.size < 2) pellizco = null;
    // si queda un dedo, sigue girando desde donde está; sin dedos, nada
    const queda = [...dedos.values()][0];
    arrastre = queda ? [queda.x, queda.y] : null;
  };
  canvas.addEventListener('pointerup', soltar);
  canvas.addEventListener('pointercancel', soltar);

  canvas.addEventListener('pointermove', e => {
    if (dedos.has(e.pointerId)) dedos.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (dedos.size === 2) {                      // pellizco: sólo acerca, nunca gira
      const d = separacion();
      if (pellizco && d > 0) { acercamiento *= d / pellizco; vista.aplicarZoom(); }
      pellizco = d;
      return;
    }
    if (!arrastre) return;
    const dx = e.clientX - arrastre[0], dy = e.clientY - arrastre[1];
    arrastre = [e.clientX, e.clientY];
    if (LIBRE) { girarPieza(dx, dy); return; }
    gx = Math.max(-TOPE_X, Math.min(TOPE_X, gx - dx * .006));
    gy = Math.max(TOPE_Y[0], Math.min(TOPE_Y[1], gy + dy * .006));
    vista.ubicar();
  });

  canvas.addEventListener('wheel', e => {
    e.preventDefault();
    acercamiento *= e.deltaY < 0 ? 1.08 : 1 / 1.08;
    vista.aplicarZoom();
  }, { passive: false });
  $('mas').addEventListener('click', () => { acercamiento *= 1.25; vista.aplicarZoom(); });
  $('menos').addEventListener('click', () => { acercamiento /= 1.25; vista.aplicarZoom(); });
  $('encuadre').addEventListener('click', () => vista.encuadre());

  return vista;
}

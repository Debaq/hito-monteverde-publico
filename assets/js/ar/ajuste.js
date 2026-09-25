// Cómo se apoya cada pieza sobre su marcador: desplazamiento en mm, giros en grados y
// escala. Es el bloque `ar` de cada pieza en el catálogo.
//
// Lo mueven los dedos del visitante (gestos.js), los botones y el panel de ?debug=1
// (calibracion.js), y todos tocan este mismo ajuste: lo que se deja acomodado es lo que
// sale al copiar y lo que hay que pegar en el catálogo para dejarlo fijo.

export const AJUSTE_BASE = { dx: 0, dy: 0, dz: 0, rx: 0, ry: 0, rz: 0, escala: 1 };
export const PASO_ZOOM = 1.08, PASO_GIRO = 5;   // el giro a 5° entra justo en los cuartos de vuelta

// Cuánto se puede agrandar y achicar respecto de como la pieza viene encuadrada. El
// tope no puede ser un número fijo: cada pieza trae su propia escala del catálogo —el
// guijarro arranca en 5,4 y los nudos en 0,14— y un límite absoluto deja a unas sin
// margen para crecer y a otras con margen de sobra.
const ZOOM_VECES = 4;

export const grados = (v, d) => ((v + d + 540) % 360) - 180;     // siempre entre -180 y 180

// Piezas que se miran por una sola cara, como la huella: los giros se acotan alrededor
// de como vienen del catálogo, para que nadie termine mirando el bloque de canto o por
// debajo. Los topes son los mismos del visor 3D: gira libre lo que tiene `camara.libre`;
// lo demás se acota con `camara.giro` de lado (ry) y `camara.rango` al inclinar y
// ladear (rx, rz), en grados. El giro de lado también se acota porque la cara de la
// huella no queda perpendicular a ese eje: girarla mucho también la da vuelta.
function topesDe(ficha, base) {
  const cam = ficha?.camara;
  if (!cam || cam.libre === true) return null;
  const inclinar = cam.rango ?? 28, lado = cam.giro ?? 46;
  return {
    rx: { centro: base.rx, r: inclinar },
    rz: { centro: base.rz, r: inclinar },
    ry: { centro: base.ry, r: lado },
  };
}
// lleva `v` al rango centro ± r, por el lado corto del círculo
const acotar = (v, { centro, r }) => grados(centro, Math.max(-r, Math.min(r, grados(v, -centro))));

/** `alCambiar` se llama después de cada cambio, para redibujar. */
export function crearAjuste(alCambiar) {
  const deFicha = ficha => {
    const v = { ...AJUSTE_BASE };
    // del bloque ar de la ficha sólo interesa la colocación; lo demás son datos del marcador
    for (const k in AJUSTE_BASE) if (typeof ficha?.ar?.[k] === 'number') v[k] = ficha.ar[k];
    return v;
  };

  const a = {
    ficha: null,
    valores: { ...AJUSTE_BASE },
    escalaBase: 1,
    topes: null,
    acotado: true,                   // la calibración de ?debug=1 lo apaga: necesita girar todo

    /** Pieza nueva: su ajuste del catálogo. */
    usar(ficha) {
      a.ficha = ficha;
      a.valores = deFicha(ficha);
      a.escalaBase = a.valores.escala;
      a.topes = topesDe(ficha, a.valores);
    },

    /** Cambia algunos valores. Sin pieza no hay nada que ajustar. */
    tocar(cambio) {
      if (!a.ficha) return;
      Object.assign(a.valores, cambio);
      if (a.topes && a.acotado)
        for (const k in a.topes) a.valores[k] = acotar(a.valores[k], a.topes[k]);
      alCambiar();
    },

    grados,                                                    // para quien arma un cambio a mano
    PASO_ZOOM, PASO_GIRO,
    limitarEscala: e => Math.min(a.escalaBase * ZOOM_VECES, Math.max(a.escalaBase / ZOOM_VECES, e)),
    zoom: f => a.tocar({ escala: a.limitarEscala(a.valores.escala * f) }),
    girar: (eje, d) => a.tocar({ [eje]: grados(a.valores[eje], d) }),

    /** De vuelta al del catálogo, no a cero pelado. */
    volverAFicha() {
      const v = deFicha(a.ficha);
      a.escalaBase = v.escala;
      a.tocar(v);
    },

    /** Todo en cero: para calibrar una pieza desde el principio. */
    aCero() {
      a.valores = { ...AJUSTE_BASE };
      alCambiar();
    },

    /** Lleva el ajuste al objeto de la pieza. */
    aplicar(obj) {
      if (!obj) return;
      const v = a.valores;
      obj.position.set(v.dx, v.dy, v.dz);                      // milímetros, como la escena
      obj.rotation.set(v.rx * Math.PI / 180, v.ry * Math.PI / 180, v.rz * Math.PI / 180);
      obj.scale.setScalar(1000 * v.escala);                    // el modelo viene en metros
    },

    /** El bloque para pegar en el catálogo. */
    texto() {
      if (!a.ficha) return '';
      // redondeado: pegar en el catálogo 1.1664 no dice nada y ensucia el archivo
      const ar = {};
      for (const k in a.valores) ar[k] = k === 'escala' ? +a.valores[k].toFixed(3) : Math.round(a.valores[k]);
      return JSON.stringify({ [a.ficha.codigo]: { ar } }, null, 1);
    },
  };
  return a;
}

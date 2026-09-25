// Dedos, rueda y teclado sobre la pieza. Mueven el mismo ajuste que los botones, no una
// vista aparte: así lo que se deja acomodado es lo que sale en el HUD y al copiar.
// Antes el pellizco y el arrastre transformaban el ancla y esos números no aparecían
// en ninguna parte.
//
// Recibe el ajuste en vez de importar ajuste.js: los módulos de ar/ los importa
// ar.html con ?v=N, y un import interno sin versión quedaría pegado en el caché.

const GRADOS_PX = .45;             // lo que gira un dedo por píxel arrastrado

/**
 * `activo()`: si los dedos mueven la pieza ahora. El visitante la mueve congelada; con
 * ?debug=1 también en vivo, que es cuando se busca cómo se apoya sobre el marcador.
 */
export function montarGestos({ lienzo, ajuste, activo, mmPorPx }) {
  const dedos = new Map();
  let giro = null, pellizco = null, centro = null, torsion = null;
  const medioEntre = v => ({ x: (v[0].x + v[1].x) / 2, y: (v[0].y + v[1].y) / 2 });
  // ángulo de la recta que une los dos dedos: girarlos en sentidos opuestos la rota
  const anguloEntre = v => Math.atan2(v[1].y - v[0].y, v[1].x - v[0].x) * 180 / Math.PI;

  lienzo.style.pointerEvents = 'auto';

  lienzo.addEventListener('pointerdown', e => {
    if (!activo()) return;
    dedos.set(e.pointerId, { x: e.clientX, y: e.clientY });
    lienzo.setPointerCapture(e.pointerId);
    if (dedos.size === 2) {
      const v = [...dedos.values()];
      pellizco = Math.hypot(v[0].x - v[1].x, v[0].y - v[1].y);
      centro = medioEntre(v);
      torsion = anguloEntre(v);
      giro = null;
    } else giro = [e.clientX, e.clientY];
  });

  const soltarDedo = e => {
    dedos.delete(e.pointerId);
    if (dedos.size < 2) { pellizco = null; centro = null; torsion = null; }
    if (dedos.size === 0) giro = null;
    // al levantar el primero de dos dedos, el que queda arranca de cero y no da un salto
    if (dedos.size === 1) { const v = [...dedos.values()][0]; giro = [v.x, v.y]; }
  };
  lienzo.addEventListener('pointerup', soltarDedo);
  lienzo.addEventListener('pointercancel', soltarDedo);

  lienzo.addEventListener('pointermove', e => {
    if (!activo()) return;
    if (dedos.has(e.pointerId)) dedos.set(e.pointerId, { x: e.clientX, y: e.clientY });
    const v0 = ajuste.valores;

    if (dedos.size === 2) {                     // dos dedos: acercar, mover de sitio y ladear
      const v = [...dedos.values()];
      const d = Math.hypot(v[0].x - v[1].x, v[0].y - v[1].y);
      const c = medioEntre(v);
      const a = anguloEntre(v);
      const cambio = {};
      if (pellizco && d > 0) cambio.escala = ajuste.limitarEscala(v0.escala * d / pellizco);
      if (centro) {
        const k = mmPorPx();
        cambio.dx = v0.dx + (c.x - centro.x) * k;
        cambio.dy = v0.dy - (c.y - centro.y) * k;      // en la escena la y crece hacia arriba
      }
      if (torsion !== null) {                          // los dedos girando en sentidos opuestos
        let da = a - torsion;
        while (da > 180) da -= 360;
        while (da < -180) da += 360;
        if (Math.abs(da) > .2) cambio.rz = ajuste.grados(v0.rz, -da);
      }
      ajuste.tocar(cambio);
      pellizco = d; centro = c; torsion = a;
      return;
    }

    if (!giro) return;                          // un dedo: girar e inclinar
    ajuste.tocar({
      ry: ajuste.grados(v0.ry, (e.clientX - giro[0]) * GRADOS_PX),
      rx: ajuste.grados(v0.rx, (e.clientY - giro[1]) * GRADOS_PX),
    });
    giro = [e.clientX, e.clientY];
  });

  // rueda del ratón y teclado: en el escritorio no hay pellizco ni dedos
  addEventListener('wheel', e => {
    if (!ajuste.ficha) return;
    e.preventDefault();
    ajuste.zoom(e.deltaY < 0 ? ajuste.PASO_ZOOM : 1 / ajuste.PASO_ZOOM);
  }, { passive: false });

  const { PASO_ZOOM, PASO_GIRO } = ajuste;
  addEventListener('keydown', e => {
    if (e.target.matches('input, select, textarea')) return;
    const acciones = {
      '+': () => ajuste.zoom(PASO_ZOOM), '=': () => ajuste.zoom(PASO_ZOOM),
      '-': () => ajuste.zoom(1 / PASO_ZOOM),
      ArrowLeft: () => ajuste.girar('ry', -PASO_GIRO), ArrowRight: () => ajuste.girar('ry', PASO_GIRO),
      ArrowUp: () => ajuste.girar('rx', PASO_GIRO), ArrowDown: () => ajuste.girar('rx', -PASO_GIRO),
    };
    if (acciones[e.key]) { e.preventDefault(); acciones[e.key](); }
  });
}

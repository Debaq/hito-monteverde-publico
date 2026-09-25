// Herramientas para dejar fijo cómo se apoya cada pieza sobre su marcador. Sólo con
// ?debug=1: los botones de la columna derecha, el panel de deslizadores y el HUD con
// números. El visitante no ve nada de esto.

const $ = id => document.getElementById(id);

const CAMPOS = [
  ['dx', 'izquierda / derecha (mm)', -120, 120, 1],
  ['dy', 'abajo / arriba (mm)', -120, 120, 1],
  ['dz', 'atrás / adelante (mm)', -120, 120, 1],
  ['ry', 'giro sobre el marcador (°)', -180, 180, 1],
  ['rx', 'inclinación (°)', -90, 90, 1],
  ['rz', 'ladeo (°)', -90, 90, 1],
  ['escala', 'escala', 0.2, 4, 0.01],
];

/**
 * `forzarPieza(codigo)`: pone una pieza sin tener el marcador delante, para calibrar
 * desde el escritorio.
 */
export function montarCalibracion({ ajuste, piezas, forzarPieza }) {
  const { PASO_ZOOM, PASO_GIRO } = ajuste;
  ajuste.acotado = false;          // para calibrar hay que poder girar la pieza entera

  // ---------- columna de botones
  $('mas').addEventListener('click', () => ajuste.zoom(PASO_ZOOM));
  $('menos').addEventListener('click', () => ajuste.zoom(1 / PASO_ZOOM));
  $('giroIzq').addEventListener('click', () => ajuste.girar('ry', -PASO_GIRO));
  $('giroDer').addEventListener('click', () => ajuste.girar('ry', PASO_GIRO));
  $('incMas').addEventListener('click', () => ajuste.girar('rx', PASO_GIRO));
  $('incMenos').addEventListener('click', () => ajuste.girar('rx', -PASO_GIRO));
  $('cero').addEventListener('click', () => ajuste.volverAFicha());
  $('copiar').addEventListener('click', async () => {
    const txt = ajuste.texto();
    if (!txt) return;
    try { await navigator.clipboard.writeText(txt); } catch { console.log(txt); }
    $('copiar').textContent = '✓';
    setTimeout(() => $('copiar').textContent = '⧉', 1200);
  });

  // ---------- panel de deslizadores
  document.body.insertAdjacentHTML('beforeend', `
    <div id="ajusteAr">
      <b id="ajustePieza">sin pieza reconocida</b>
      <label>probar una pieza sin tener el marcador delante</label>
      <select id="piezaAjuste">
        <option value="">— la que se reconozca —</option>
        ${piezas.map(p => `<option value="${p.codigo}">${p.denominacion}` +
                          `${p.media?.modelo_movil ? '' : ' (foto)'}</option>`).join('')}
      </select>
      ${CAMPOS.map(([k, txt, min, max, paso]) => `
        <label>${txt} <span data-v="${k}">0</span></label>
        <input type="range" data-k="${k}" min="${min}" max="${max}" step="${paso}" value="0">`).join('')}
      <div class="fila">
        <button class="btn" id="cerarAjuste">Volver a cero</button>
        <button class="btn" id="copiarAjuste">Copiar</button>
      </div>
      <pre id="salidaAjuste">—</pre>
    </div>`);

  $('piezaAjuste').addEventListener('change', e => { if (e.target.value) forzarPieza(e.target.value); });

  const controles = [...document.querySelectorAll('#ajusteAr input')];
  for (const c of controles)
    c.addEventListener('input', () => ajuste.tocar({ [c.dataset.k]: +c.value }));
  $('cerarAjuste').addEventListener('click', () => ajuste.aCero());
  $('copiarAjuste').addEventListener('click', () => {
    navigator.clipboard?.writeText($('salidaAjuste').textContent);
    $('copiarAjuste').textContent = 'Copiado';
    setTimeout(() => $('copiarAjuste').textContent = 'Copiar', 1200);
  });

  // el HUD crece con las líneas de lectura: el panel se acomoda debajo en vez de taparlo
  const acomodar = () => $('ajusteAr').style.top = `${$('hud').getBoundingClientRect().bottom + 8}px`;
  new ResizeObserver(acomodar).observe($('hud'));
  acomodar();

  const cal = {
    /** Hay pieza nueva o cambió su ajuste: los deslizadores y el texto la siguen. */
    refrescar() {
      const f = ajuste.ficha;
      $('ajustePieza').textContent = f ? `${f.codigo} — ${f.denominacion}` : 'sin pieza reconocida';
      for (const c of controles) {
        const v = ajuste.valores[c.dataset.k];
        c.value = v;
        document.querySelector(`[data-v="${c.dataset.k}"]`).textContent =
          c.dataset.k === 'escala' ? v.toFixed(2) : Math.round(v);
      }
      $('salidaAjuste').textContent = ajuste.texto() || '—';
      if (f) $('tocar').classList.add('on');
    },

    /** El HUD con números: qué se lee del marcador y el ajuste en curso. */
    textoHud({ ids, fps, lectura, buscar }) {
      const hay = ids.length || !buscar;
      let txt = hay
        ? `marcadores  ${ids.length ? ids.join(' · ') : '—'}\n` +
          `pieza       ${ajuste.ficha?.denominacion || '—'}\n` +
          `fps         ${fps.toFixed(0)}`
        : `apunta a cualquier código de la ruta${buscar ? `\nel de esta pieza es ${buscar}` : ''}`;

      // el ajuste en curso: es lo que hay que copiar al catálogo para dejarlo fijo
      const v = ajuste.valores;
      if (ajuste.ficha)
        txt += `\nescala      ${v.escala.toFixed(2)}×\n` +
               `giro        ${v.ry.toFixed(0)}° · incl ${v.rx.toFixed(0)}° · lad ${v.rz.toFixed(0)}°\n` +
               `posición    ${v.dx.toFixed(0)}, ${v.dy.toFixed(0)}, ${v.dz.toFixed(0)} mm`;

      // además cómo se está leyendo el marcador: sirve para saber si lo que baila es la
      // pieza o la lectura de la pose
      if (lectura)
        txt += `\nmarcador    id ${lectura.id} (${lectura.tipo})\n` +
               `distancia   ${lectura.dist.toFixed(0)} mm · ${lectura.lado.toFixed(0)} px de lado\n` +
               `pose        ${lectura.rx.toFixed(0)}° / ${lectura.ry.toFixed(0)}° / ${lectura.rz.toFixed(0)}°`;
      return txt;
    },
  };
  cal.refrescar();
  return cal;
}

// Panel para fijar el encuadre de cada pieza y copiarlo al catálogo. Sólo con ?debug=1.

const $ = id => document.getElementById(id);

export function montarCalibracion({ ficha, cam, vista }) {
  document.body.insertAdjacentHTML('beforeend', `
    <div id="ajuste">
      <b>${ficha.codigo}</b>
      <label>zoom <span id="nivelZoom">—</span></label>
      <input type="range" id="sZoom" min="0.5" max="6" step="0.05" value="${cam.zoom ?? 1}">
      <label>distancia base <span id="vDist">${cam.distancia ?? 1.45}</span></label>
      <input type="range" id="sDist" min="0.8" max="3" step="0.05" value="${cam.distancia ?? 1.45}">
      <button class="btn" id="copiarCam">Copiar para el catálogo</button>
      <pre id="salidaCam">—</pre>
    </div>`);

  const refrescar = () => {
    $('salidaCam').textContent = JSON.stringify({
      [ficha.codigo]: { camara: { ...cam, zoom: +vista.acercamiento.toFixed(2),
                                  distancia: +(+$('sDist').value).toFixed(2) } },
    }, null, 1);
  };
  // cada cambio de zoom, venga de donde venga, se refleja en el panel
  vista.alAjustar = () => {
    $('nivelZoom').textContent = vista.acercamiento.toFixed(2) + '×';
    $('sZoom').value = vista.acercamiento;             // el control sigue al zoom real
    refrescar();
  };
  $('sZoom').addEventListener('input', e => { vista.acercamiento = +e.target.value; vista.aplicarZoom(); });
  $('sDist').addEventListener('input', e => {
    $('vDist').textContent = e.target.value;
    vista.fijarDistancia(+e.target.value);
    vista.ubicar(); vista.aplicarZoom();
  });
  $('copiarCam').addEventListener('click', () => {
    navigator.clipboard?.writeText($('salidaCam').textContent);
    $('copiarCam').textContent = 'Copiado';
    setTimeout(() => $('copiarCam').textContent = 'Copiar para el catálogo', 1200);
  });
  refrescar();
}

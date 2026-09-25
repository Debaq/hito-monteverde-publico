// El modelo completo, que reemplaza al liviano sin que se note.
//
// Primero entra el modelo liviano —medio mega, aparece casi al instante— y el completo
// se baja después, en segundo plano. Sólo en pantalla grande, con buena conexión, y
// recién cuando la persona se quedó mirando o tocó la pieza: si pasa de largo, no gasta
// nada.

const $ = id => document.getElementById(id);

/**
 * `nube`: los puntos de la pieza, si tiene, que comparten textura.
 * `mapaRugosidad`: de materiales.js, para rehacer la rugosidad con la textura nueva.
 */
export function montarDetalle({ lienzo, cargador, url, liviano, malla, matTextura, nube, mapaRugosidad, pedir }) {
  const chico = innerWidth * Math.min(devicePixelRatio, 2) < 1500;
  const red = navigator.connection || {};
  const conexionPobre = red.saveData || /^(slow-)?2g$/.test(red.effectiveType || '');
  let pedido = false;

  function traer() {
    if (pedido || chico || conexionPobre || liviano) return;
    pedido = true;                                 // una sola vez
    document.body.insertAdjacentHTML('beforeend',
      '<div id="detalle" class="chip sage">cargando el detalle…</div>');
    cargador.loadAsync(url).then(g => {
      let fina = null;
      g.scene.traverse(o => { if (o.isMesh && !fina) fina = o; });
      if (!fina) return;
      malla.geometry.dispose();
      malla.geometry = fina.geometry;
      // La textura va al material de textura, no a malla.material: si en ese momento
      // estaba puesto el modo relieve, malla.material es el de relieve y le quedaba
      // pegada la textura encima, con lo que el relieve no volvía nunca.
      if (fina.material.map) {
        matTextura.map?.dispose();
        matTextura.map = fina.material.map;
        matTextura.roughnessMap = mapaRugosidad(fina.material.map.image) ?? matTextura.roughnessMap;
        matTextura.needsUpdate = true;
        if (nube) nube.material.needsUpdate = true;
      }
      pedir();
      $('detalle')?.remove();
    }).catch(() => $('detalle')?.remove());
  }

  lienzo.addEventListener('pointerdown', traer, { once: true });
  setTimeout(traer, 2500);                         // o si se queda mirando
}

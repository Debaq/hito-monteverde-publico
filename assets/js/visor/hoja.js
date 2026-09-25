// La hoja de abajo con la ficha del catálogo. Se abre arrastrándola o tocándola. Antes
// había un botón "Ver la ficha" en una barra que, además, tapaba la agarradera: tocarla
// no hacía nada.

const $ = id => document.getElementById(id);
const ASOMO = 62;                  // lo que se ve de la hoja cerrada, en px

/** La ficha tal cual está en el catálogo. */
export function llenarFicha(f) {
  $('titulo').textContent = f.denominacion;
  $('chipPieza').textContent = f.denominacion;
  $('tituloHoja').textContent = f.denominacion;
  $('linkFicha').href = `pieza.html?id=${encodeURIComponent(f.codigo)}`;
  document.title = `${f.denominacion} en 3D — Monte Verde`;
  $('cita').innerHTML = `«${f.descripcion}»<small>FICHA DEL CATÁLOGO · ${f.tipo_objeto} · ${f.sitio}</small>`;
  $('datos').innerHTML = [
    ['Tipo de objeto', f.tipo_objeto], ['Material', f.categoria_material],
    ['Sitio', f.sitio], ['Localidad', f.localidad], ['Página del catálogo', f.pagina],
  ].filter(([, v]) => v != null && v !== '')
   .map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
}

export function montarHoja() {
  const hoja = $('hoja'), tirador = $('tirador');
  let abierta = false, y0 = null, alto = 0, corrida = 0;

  const colocar = px => {
    hoja.style.transition = px == null ? '' : 'none';
    hoja.style.transform = px == null ? '' : `translateY(${px}px)`;
  };
  const abrir = si => {
    abierta = si;
    hoja.classList.toggle('abierta', si);
    document.body.classList.toggle('leyendo', si);   // esconde rueda de luz y zoom
    $('pistaHoja').textContent = si ? 'desliza para cerrar' : 'ficha del catálogo';
    colocar(null);
  };

  tirador.addEventListener('pointerdown', e => {
    if (e.target.closest('button')) return;            // el molde tiene lo suyo
    alto = hoja.offsetHeight; y0 = e.clientY;
    corrida = abierta ? 0 : alto - ASOMO;
    tirador.setPointerCapture(e.pointerId);
  });
  tirador.addEventListener('pointermove', e => {
    if (y0 == null) return;
    const base = abierta ? 0 : alto - ASOMO;
    corrida = Math.max(0, Math.min(alto - ASOMO, base + (e.clientY - y0)));
    colocar(corrida);
  });
  const soltar = e => {
    if (y0 == null) return;
    const movido = Math.abs(e.clientY - y0);
    y0 = null;
    // un toque alterna; un arrastre queda del lado al que lo llevaron
    abrir(movido < 6 ? !abierta : corrida < (alto - ASOMO) / 2);
  };
  tirador.addEventListener('pointerup', soltar);
  tirador.addEventListener('pointercancel', soltar);
}

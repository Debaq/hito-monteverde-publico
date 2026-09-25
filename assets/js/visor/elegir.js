// Entrar al visor sin pieza elegida no es un error: se ofrece la lista y se entra de una.

export function mostrarLista(catalogo) {
  const con3d = catalogo.piezas.filter(p => p.media?.modelo);
  document.getElementById('cargando').remove();
  document.body.insertAdjacentHTML('beforeend', `
    <div class="elegir">
      <div class="wrap">
        <h1>Piezas en 3D</h1>
        <p class="muted">${con3d.length} de ${catalogo.piezas.length} piezas tienen modelo. Elige una.</p>
        <div class="rejilla">
          ${con3d.map(p => `
            <a href="visor.html?id=${encodeURIComponent(p.codigo)}">
              <img src="${p.media.imagen_movil}" alt="" loading="lazy">
              <b>${p.denominacion}</b>
              <span>${p.tipo_objeto || ''}</span>
            </a>`).join('')}
        </div>
        <a class="btn" style="margin-top:18px;display:inline-flex" href="index.html">Volver al inicio</a>
      </div>
    </div>`);
}

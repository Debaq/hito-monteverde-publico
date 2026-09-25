// La luz rasante, que es la que revela el relieve: se mueve con el sensor del teléfono
// o, si no hay, con el dial de la esquina.
//
// Recibe activarSensor y esTactil (de sensor.js) en vez de importarlos: los módulos los
// importa visor.html con ?v=N, y un import interno sin versión quedaría en el caché.

const $ = id => document.getElementById(id);

/** `radio()`: a qué distancia va la luz. `hayRelieve`: si la pieza tiene modo relieve. */
export function montarLuz({ rasante, radio, pedir, hayRelieve, activarSensor, esTactil }) {
  let azimut = 135, elevacion = 16;
  let apagarSensor = null;

  const ubicar = () => {
    pedir();
    const a = azimut * Math.PI / 180, e = elevacion * Math.PI / 180;
    const R = radio();
    rasante.position.set(R * Math.cos(e) * Math.cos(a), R * Math.sin(e),
                         R * Math.cos(e) * Math.sin(a));
    $('rayo').style.transform = `rotate(${-azimut}deg)`;
  };

  const desdeDial = e => {
    const r = $('dial').getBoundingClientRect();
    azimut = Math.atan2(-(e.clientY - r.top - r.height / 2), e.clientX - r.left - r.width / 2) * 180 / Math.PI;
    ubicar();
  };
  $('dial').addEventListener('pointerdown', e => { $('dial').setPointerCapture(e.pointerId); desdeDial(e); });
  $('dial').addEventListener('pointermove', e => { if (e.buttons) desdeDial(e); });

  async function alternarSensor() {
    if (apagarSensor) {
      apagarSensor(); apagarSensor = null;
      $('capaSensor').setAttribute('aria-pressed', 'false');
      $('dial').classList.add('on');
      return;
    }
    const r = await activarSensor(({ azimut: a, elevacion: e }) => {
      azimut = a; elevacion = e; ubicar();
    });
    if (r.error) { $('capaSensor').classList.add('no'); $('dial').classList.add('on'); return; }
    apagarSensor = r.apagar;
    $('capaSensor').setAttribute('aria-pressed', 'true');
    $('capaSensor').classList.remove('no');
    $('dial').classList.remove('on');
    $('bajada').textContent = 'Gira la pieza con el dedo. Inclina el teléfono para mover la luz.';
  }
  $('capaSensor').addEventListener('click', alternarSensor);

  // El permiso de iOS necesita un gesto, y el chip "Luz con el teléfono" de la fila de
  // capas ya lo es. Antes se abría un cartel a pantalla completa preguntando antes de
  // dejar ver la pieza: la rueda de luz queda a la vista y funciona sin permiso alguno.
  if (hayRelieve) {
    $('dial').classList.add('on');
    if (!esTactil()) $('capaSensor').style.display = 'none';
  } else {
    // sin modo relieve, mover la luz no aporta nada: se esconde la rueda y el sensor
    $('capaSensor').style.display = 'none';
    $('dial').style.display = 'none';
  }

  return { ubicar, sensorPrendido: () => apagarSensor !== null };
}

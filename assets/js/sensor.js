// Sensor de orientación, igual en todas las páginas que lo usan.
//
// Tres cosas que hay que respetar, y que explican por qué esto no puede ser una línea:
//   · iOS exige que el permiso se pida desde un gesto del usuario, no al cargar;
//   · el sensor sólo funciona en contexto seguro (HTTPS o localhost);
//   · en computador no existe, así que ni se ofrece.

export const esTactil = () =>
  matchMedia('(pointer: coarse)').matches || navigator.maxTouchPoints > 1;

export const puedeSensor = () =>
  esTactil() && isSecureContext && typeof DeviceOrientationEvent !== 'undefined';

/**
 * Pide permiso y empieza a escuchar. Devuelve una función para apagarlo, o null si no se pudo.
 * `alMover` recibe {azimut, elevacion} ya acotados, listos para usar.
 */
export async function activarSensor(alMover) {
  if (!isSecureContext) return { error: 'El sensor necesita una conexión segura (HTTPS).' };
  try {
    if (typeof DeviceOrientationEvent?.requestPermission === 'function') {
      const r = await DeviceOrientationEvent.requestPermission();
      if (r !== 'granted') return { error: 'Sin permiso para usar el sensor de orientación.' };
    }
  } catch {
    return { error: 'Este dispositivo no permite usar el sensor.' };
  }

  let visto = false;
  const escucha = e => {
    if (e.beta == null) return;
    visto = true;
    alMover({
      // inclinación lateral -> dirección; inclinación frontal -> altura
      azimut: 135 - Math.max(-60, Math.min(60, e.gamma ?? 0)) * 3,
      elevacion: Math.max(6, Math.min(55, 60 - Math.abs(Math.max(0, Math.min(90, e.beta)) - 30))),
      alpha: e.alpha, beta: e.beta, gamma: e.gamma,
    });
  };
  addEventListener('deviceorientation', escucha);

  await new Promise(r => setTimeout(r, 900));
  if (!visto) {
    removeEventListener('deviceorientation', escucha);
    return { error: 'Este dispositivo no entrega datos de orientación.' };
  }
  return { apagar: () => removeEventListener('deviceorientation', escucha) };
}

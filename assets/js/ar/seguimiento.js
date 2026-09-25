// Entre lecturas del marcador: cómo sigue el ancla a la pose y cuándo la pieza está
// quieta como para congelarse sola.
import * as THREE from 'three';

/** Lleva el ancla hacia la última pose leída, cuadro a cuadro. */
export function crearSeguimiento(ancla) {
  const pos = new THREE.Vector3(), rot = new THREE.Euler(), destino = new THREE.Vector3();
  let objetivo = null, listo = false;

  return {
    /** Pose nueva, o null si se perdió el marcador. */
    apuntar(o) { objetivo = o; },
    /** Se perdió el marcador: la pieza se esconde y la próxima pose entra de golpe. */
    soltar() { objetivo = null; listo = false; ancla.visible = false; },

    paso() {
      if (!objetivo) return;
      destino.set(objetivo.x, objetivo.y, objetivo.z);
      if (!listo) { pos.copy(destino); rot.set(objetivo.rx, objetivo.ry, objetivo.rz); listo = true; }

      // Suavizado adaptativo: si el marcador casi no se movió, se filtra fuerte y el
      // temblor desaparece; si se movió de verdad, se sigue rápido y no queda blando. Un
      // factor fijo no puede hacer las dos cosas. Corre en cada cuadro aunque la lectura
      // llegue a 15 Hz: es lo que rellena el hueco entre lecturas y evita los saltos.
      const k = Math.min(.6, Math.max(.08, pos.distanceTo(destino) / 40));
      pos.lerp(destino, k);
      const acercar = (a, b) => {                      // por el camino corto, sin saltos de 2π
        let d = b - a;
        while (d > Math.PI) d -= 2 * Math.PI;
        while (d < -Math.PI) d += 2 * Math.PI;
        return a + d * k;
      };
      rot.set(acercar(rot.x, objetivo.rx), acercar(rot.y, objetivo.ry), acercar(rot.z, objetivo.rz));
      ancla.position.copy(pos);
      ancla.rotation.copy(rot);
      ancla.visible = true;
    },
  };
}

const MS_QUIETA = 2000;              // cuánto tiene que estar quieta antes de congelarse sola
const QUIETA_DIST = .06;             // se mueve menos que esto (fracción de la distancia): quieta
const QUIETA_GRADOS = 12;            // y gira menos que esto

/**
 * Cuenta cuánto lleva quieta la pieza. Antes se congelaba a los 0,8 s de ver el
 * marcador, aunque el teléfono todavía se estuviera acomodando. Ahora hacen falta 2 s
 * sin moverse; si se mueve, la cuenta vuelve a empezar.
 */
export function crearQuietud() {
  let desde = 0, base = null;
  const reiniciar = () => { desde = 0; base = null; };

  return {
    reiniciar,
    /** Avance de 0 a 1; en 1, ya estuvo quieta el tiempo necesario. */
    medir(o, distancia, ahora) {
      const quieta = base &&
        Math.hypot(o.x - base.x, o.y - base.y, o.z - base.z) < distancia * QUIETA_DIST &&
        ['rx', 'ry', 'rz'].every(k => {
          const d = Math.abs(o[k] - base[k]) * 180 / Math.PI % 360;
          return Math.min(d, 360 - d) < QUIETA_GRADOS;
        });
      if (!desde || !quieta) { desde = ahora; base = { ...o }; }
      return Math.min(1, (ahora - desde) / MS_QUIETA);
    },
  };
}

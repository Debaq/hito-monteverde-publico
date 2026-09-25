// Escena 3D transparente sobre el video de la cámara.
//
// Todo va en milímetros: el ancla sigue al marcador y de ella cuelga la pieza, que
// lleva su propio ajuste (ajuste.js). La cámara 3D la alinea deteccion.js con lo que
// se ve del video.
import * as THREE from 'three';

export function crearEscena(lienzo) {
  const renderer = new THREE.WebGLRenderer({ canvas: lienzo, alpha: true, antialias: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;

  const scene = new THREE.Scene();
  // la cámara imita la del teléfono: el campo se ajusta con la distancia focal estimada
  const camara = new THREE.PerspectiveCamera(40, innerWidth / innerHeight, 1, 5000);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x444433, 2.2));
  const sol = new THREE.DirectionalLight(0xfff2de, 2.4);
  sol.position.set(200, 400, 300);
  scene.add(sol);

  const ancla = new THREE.Group();          // sigue al marcador; el modelo cuelga de aquí
  scene.add(ancla);

  return {
    camara, ancla,
    dibujar: () => renderer.render(scene, camara),

    medir() {
      renderer.setSize(innerWidth, innerHeight);
      camara.aspect = innerWidth / innerHeight;
      camara.updateProjectionMatrix();
    },

    // Mover un dedo tiene que valer lo mismo en pantalla que en la escena, si no el
    // arrastre se siente pegajoso de cerca y disparado de lejos: la pieza está a `z` mm.
    mmPorPx() {
      const z = Math.abs(ancla.position.z) || 400;
      return 2 * z * Math.tan(camara.fov * Math.PI / 360) / innerHeight;
    },
  };
}

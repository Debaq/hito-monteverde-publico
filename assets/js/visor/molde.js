// El molde de la huella, en su propia escena y su propio lienzo. Gira solo hasta que lo
// tocan.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

/**
 * Arma el molde en `lienzo`. Devuelve `correr(si)`, que prende o apaga su bucle, y
 * `dibujar()`, que lo dibuja en el momento y devuelve el lienzo, para sacarle una foto.
 */
export async function armarMolde(lienzo, { url, draco }) {
  const r2 = new THREE.WebGLRenderer({ canvas: lienzo, antialias: true });
  r2.setPixelRatio(Math.min(devicePixelRatio, 2));
  const sc = new THREE.Scene(); sc.background = new THREE.Color(0x16110c);
  const cam = new THREE.PerspectiveCamera(34, innerWidth / innerHeight, .01, 20);
  const luz = new THREE.DirectionalLight(0xfff2de, 3.6);
  const contra = new THREE.DirectionalLight(0xb7b7a4, .55);
  sc.add(luz, contra, new THREE.AmbientLight(0xffffff, .10),
         new THREE.HemisphereLight(0x8c8c7a, 0x16110c, .18));

  const g = await new GLTFLoader().setDRACOLoader(draco).loadAsync(url);
  const obj = g.scene;
  obj.traverse(o => { if (o.isMesh) o.material = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: .88, metalness: 0 }); });
  sc.add(obj);
  const cj = new THREE.Box3().setFromObject(obj), t2 = cj.getSize(new THREE.Vector3());
  obj.position.sub(cj.getCenter(new THREE.Vector3()));
  const R = t2.length() * 1.95;
  luz.position.set(R * Math.cos(.24) * Math.cos(2.36), R * Math.sin(.24), R * Math.cos(.24) * Math.sin(2.36));
  contra.position.set(R * .8, -R * .2, -R * .7);

  let mx = -.35, my = .75, quieto = true, ult = null, sentido = 1;
  const ub = () => { cam.position.set(R * Math.cos(my) * Math.sin(mx), R * Math.sin(my),
                                      R * Math.cos(my) * Math.cos(mx)); cam.lookAt(0, 0, 0); };
  lienzo.addEventListener('pointerdown', e => { ult = [e.clientX, e.clientY]; quieto = false; lienzo.setPointerCapture(e.pointerId); });
  lienzo.addEventListener('pointerup', () => ult = null);
  lienzo.addEventListener('pointermove', e => {
    if (!ult) return;
    mx = Math.max(-.95, Math.min(.95, mx - (e.clientX - ult[0]) * .008));
    my = Math.max(.15, Math.min(1.15, my + (e.clientY - ult[1]) * .008));
    ult = [e.clientX, e.clientY]; ub();
  });
  const medir = () => { r2.setSize(innerWidth, innerHeight); cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); };
  addEventListener('resize', medir); medir(); ub();

  // El molde gira solo, así que este bucle sí tiene que dibujar cada cuadro. Pero
  // mientras se mira la huella el molde está oculto: si el bucle sigue, quedan dos
  // contextos WebGL dibujando y uno no se ve.
  const bucle = () => {
    if (quieto) { mx += .004 * sentido; if (Math.abs(mx) > .95) sentido *= -1; ub(); }
    r2.render(sc, cam);
  };
  return {
    correr: si => r2.setAnimationLoop(si ? bucle : null),
    dibujar() { r2.render(sc, cam); return lienzo; },
  };
}

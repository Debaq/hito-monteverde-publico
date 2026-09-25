// Lo que se pone sobre el marcador: el modelo 3D de la pieza, o su fotografía si no
// tiene modelo. Y el cambio a nube de puntos, que sale de la misma malla.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const draco = new DRACOLoader().setDecoderPath('assets/vendor/three/addons/libs/draco/');
const cargador = new GLTFLoader().setDRACOLoader(draco);
const texturas = new THREE.TextureLoader();
const cache = new Map();

/** El objeto de una pieza, centrado. Se carga una vez y queda guardado. */
export async function cargarPieza(ficha) {
  if (cache.has(ficha.codigo)) return cache.get(ficha.codigo);
  let obj;
  if (ficha.media?.modelo_movil) {
    const g = await cargador.loadAsync(ficha.media.modelo_movil);
    const modelo = g.scene;
    const caja = new THREE.Box3().setFromObject(modelo);
    modelo.position.sub(caja.getCenter(new THREE.Vector3()));
    obj = new THREE.Group();
    obj.add(modelo);
  } else {
    obj = await lamina(ficha);
  }
  cache.set(ficha.codigo, obj);
  return obj;
}

// Cinco piezas del recorrido no tienen modelo 3D. De esas se monta la fotografía de la
// ficha sobre el marcador, al tamaño que dan sus dimensiones. Antes el marcador se
// reconocía pero no se cargaba nada, así que seguía en pantalla la pieza anterior y
// parecía un error de lectura.
async function lamina(ficha) {
  const tex = await texturas.loadAsync(ficha.media.imagen_movil || ficha.media.imagen);
  tex.colorSpace = THREE.SRGBColorSpace;

  const d = ficha.dimensiones || {};
  const mayor = Math.max(d.largo || 0, d.ancho || 0) || 15;        // cm; sin dato, 15 cm
  const prop = tex.image.height / tex.image.width;
  // el lado largo de la foto lleva la medida larga de la pieza
  const alto = prop >= 1 ? mayor / 100 : (mayor / 100) * prop;     // metros: la escena x1000
  const ancho = prop >= 1 ? alto / prop : mayor / 100;

  const plano = (w, h, mat) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat);
  const foto = plano(ancho, alto, new THREE.MeshBasicMaterial(
    { map: tex, side: THREE.DoubleSide, toneMapped: false }));
  const papel = plano(ancho * 1.07, alto * 1.05, new THREE.MeshBasicMaterial(
    { color: 0xf6f1e8, side: THREE.DoubleSide, toneMapped: false }));
  papel.position.z = -0.0006;

  const envoltorio = new THREE.Group();
  envoltorio.add(papel, foto);
  return envoltorio;
}

// ---------- nube de puntos
// La misma del visor 3D (assets/js/nube.js), coloreada por altura. Antes aquí se armaba
// otra, con el color de la foto: se veía como una textura con granos y no mostraba el
// hueco. La función llega de ar.html, que es quien importa los módulos con versión.
// Se arma una sola vez por pieza, la primera vez que la piden.
//
// Sobre el video, los puntos sueltos se pierden contra el suelo o el cartel. Detrás de
// ellos queda la misma malla, pero como una silueta casi negra: oscurece sólo la forma
// de la pieza y el resto de la cámara sigue igual. La silueta se corre un poco hacia
// atrás en profundidad para no tapar los puntos, que están justo sobre su superficie,
// y sigue tapando los de la cara de atrás, así no se ve la pieza de lado a lado.
const nubes = new Map();
const fondoNube = new THREE.MeshBasicMaterial({
  color: 0x0d0a07, transparent: true, opacity: .88,
  polygonOffset: true, polygonOffsetFactor: 2, polygonOffsetUnits: 2,
});

/**
 * Muestra la pieza como puntos o como sólido. `crear(malla)` arma la nube la primera
 * vez. Devuelve la nube, o null si la pieza no tiene malla o nube que mostrar.
 */
export function verNube(obj, si, crear) {
  if (!obj) return null;
  if (!nubes.has(obj)) {
    if (!si) return null;                          // volver a sólido no obliga a armar la nube
    let malla = null;
    obj.traverse(o => { if (!malla && o.isMesh) malla = o; });
    nubes.set(obj, malla && { malla, material: malla.material, pts: crear(malla) });
  }
  const par = nubes.get(obj);
  if (!par?.pts) return null;
  par.malla.material = si ? fondoNube : par.material;
  par.pts.visible = si;
  return par.pts;
}

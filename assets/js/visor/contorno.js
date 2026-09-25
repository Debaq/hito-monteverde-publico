// El contorno que trazó el equipo, apoyado sobre la superficie escaneada.
//
// `datos.contorno`: puntos { xy: [x, z] } en milímetros desde la esquina mínima del
// bloque. Cada uno se baja con un rayo hasta tocar la malla.
import * as THREE from 'three';

export function contornoSobre({ scene, malla, caja, centro, tam, datos }) {
  scene.updateMatrixWorld(true);        // sin esto el rayo usa matrices viejas y no toca la malla
  const esquina = caja.min.clone();                 // esquina del bloque, en coordenadas de escena
  const rc = new THREE.Raycaster();
  let faltantes = 0;
  const alto = caja.max.y - centro.y + .2;
  const pts = datos.contorno.map(p => {
    const x = esquina.x - centro.x + p.xy[0] * .001;
    const z = esquina.z - centro.z + p.xy[1] * .001;
    rc.set(new THREE.Vector3(x, alto, z), new THREE.Vector3(0, -1, 0));
    const hit = rc.intersectObject(malla, false)[0];   // sólo la malla: la nube desvía el rayo
    if (!hit) faltantes++;
    return new THREE.Vector3(x, (hit ? hit.point.y : 0) + tam.y * .015, z);
  });
  if (faltantes) console.warn(`contorno: ${faltantes} puntos sin superficie debajo`);
  // se dibuja por encima de todo: si respeta profundidad, el reborde del hueco la tapa
  const l = new THREE.Line(new THREE.BufferGeometry().setFromPoints([...pts, pts[0]]),
                           new THREE.LineBasicMaterial({ color: 0xe9a93c, depthTest: false }));
  l.renderOrder = 10;
  l.visible = false;
  scene.add(l);
  return l;
}

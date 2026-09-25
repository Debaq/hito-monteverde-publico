// Los dos aspectos de la pieza: la textura del escaneo y el relieve, gris y mate, que
// sólo muestra la forma bajo la luz rasante.
import * as THREE from 'three';

/** Deja mate el material de fotogrametría: la textura ya trae su propia luz. */
export function prepararTextura(mat) {
  mat.roughness = 1;
  mat.metalness = 0;
  mat.envMapIntensity = .55;
  if ('specularIntensity' in mat) mat.specularIntensity = 0;
  if (mat.map?.image) {
    mat.roughnessMap = mapaRugosidad(mat.map.image);
    mat.roughness = 1;
  }
  mat.needsUpdate = true;
  return mat;
}

export const crearRelieve = () => new THREE.MeshStandardMaterial({
  color: 0xc9bfae, roughness: 1, metalness: 0, envMapIntensity: 0,
});

// Mapa de rugosidad derivado de la propia textura: las zonas con grano fino son porosas
// (mate) y las lisas, pulidas o húmedas (algo más brillantes). Se calcula aquí y no en el
// archivo para no rehacer los modelos.
export function mapaRugosidad(imagen, lado = 512) {
  if (!imagen?.width) return null;              // textura aún sin decodificar
  const cv = document.createElement('canvas');
  cv.width = cv.height = lado;
  const ctx = cv.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(imagen, 0, 0, lado, lado);
  const src = ctx.getImageData(0, 0, lado, lado);
  const lum = new Float32Array(lado * lado);
  for (let i = 0, q = 0; i < lum.length; i++, q += 4)
    lum[i] = (src.data[q] * .299 + src.data[q+1] * .587 + src.data[q+2] * .114) / 255;

  // Desvío local contra el promedio de un entorno de 5 px = cuánto grano hay.
  //
  // El promedio sale de una tabla de sumas acumuladas: cualquier ventana, del tamaño
  // que sea, se resuelve con cuatro lecturas. Recorrer los 25 vecinos de cada píxel
  // eran 6,5 millones de lecturas en el hilo principal, justo en el instante en que
  // aparece la pieza. El resultado es el mismo, incluidos los bordes recortados.
  const W = lado + 1;
  const sat = new Float64Array(W * W);
  for (let y = 0; y < lado; y++) {
    let fila = 0;
    for (let x = 0; x < lado; x++) {
      fila += lum[y * lado + x];
      sat[(y + 1) * W + (x + 1)] = sat[y * W + (x + 1)] + fila;
    }
  }

  const out = ctx.createImageData(lado, lado);
  const R = 2;
  for (let y = 0; y < lado; y++) {
    const y0 = Math.max(0, y - R), y1 = Math.min(lado, y + R + 1);
    for (let x = 0; x < lado; x++) {
      const x0 = Math.max(0, x - R), x1 = Math.min(lado, x + R + 1);
      const suma = sat[y1 * W + x1] - sat[y0 * W + x1] - sat[y1 * W + x0] + sat[y0 * W + x0];
      const n = (x1 - x0) * (y1 - y0);
      const i = y * lado + x;
      const grano = Math.min(1, Math.abs(lum[i] - suma / n) * 9);
      const rug = .60 + .40 * grano;            // liso 0.60, granulado 1.00
      const q = i * 4;
      out.data[q] = 0;                          // R: sin uso
      out.data[q+1] = rug * 255;                // G: rugosidad, como manda glTF
      out.data[q+2] = 0;                        // B: metalicidad, siempre cero
      out.data[q+3] = 255;
    }
  }
  ctx.putImageData(out, 0, 0);
  const t = new THREE.CanvasTexture(cv);
  t.flipY = false;                              // igual que la textura de color en glTF
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  return t;
}

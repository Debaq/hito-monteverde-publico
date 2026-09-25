// Nube de puntos coloreada por altura, que es como se lee una nube en registro. La usan
// el visor 3D y la cámara AR: es la misma nube en los dos lados.
//
// `nube` es el bloque de la ficha: { modo: 'altura' | 'plano', rango_mm: [min, max] }.
// Sin modo, la pieza no tiene nube.
import * as THREE from 'three';

// rampa perceptual tipo viridis: cada altura, un color distinguible
const RAMPA = [[0.27,0.00,0.33],[0.23,0.32,0.55],[0.13,0.57,0.55],
               [0.37,0.79,0.38],[0.99,0.91,0.15]];

/**
 * `tamano`: el del punto, en unidades de la escena. El visor trabaja en metros y le
 * sirve el de siempre; la AR trabaja en milímetros y con la pieza escalada, así que
 * pasa el suyo.
 */
export function nubePorAltura(malla, nube, { tamano = 0.0011 } = {}) {
  if (!nube?.modo) return null;
  const g = malla.geometry.clone();
  const pos = g.attributes.position;

  // Se mide la altura contra el plano del bloque, no contra el eje Y absoluto: si no,
  // la inclinación del bloque manda y el punto más bajo cae en una esquina, no en la huella.
  // El plano se ajusta por mínimos cuadrados y se reajusta descartando lo hundido,
  // para que represente la superficie de alrededor y no el hueco.
  const idx = [];
  for (let i = 0; i < pos.count; i += 5) idx.push(i);
  const ajustar = sub => {
    let sxx=0, szz=0, sxz=0, sx=0, sz=0, n=0, sxy=0, szy=0, sy=0;
    for (const i of sub) {
      const x = pos.getX(i), z = pos.getZ(i), y = pos.getY(i);
      sxx+=x*x; szz+=z*z; sxz+=x*z; sx+=x; sz+=z; sxy+=x*y; szy+=z*y; sy+=y; n++;
    }
    const A = [[sxx,sxz,sx],[sxz,szz,sz],[sx,sz,n]], b = [sxy,szy,sy];
    for (let c = 0; c < 3; c++) {                       // eliminación de Gauss, 3x3
      let piv = c;
      for (let r = c+1; r < 3; r++) if (Math.abs(A[r][c]) > Math.abs(A[piv][c])) piv = r;
      [A[c], A[piv]] = [A[piv], A[c]]; [b[c], b[piv]] = [b[piv], b[c]];
      for (let r = 0; r < 3; r++) {
        if (r === c || !A[c][c]) continue;
        const f = A[r][c] / A[c][c];
        for (let k = c; k < 3; k++) A[r][k] -= f * A[c][k];
        b[r] -= f * b[c];
      }
    }
    return [b[0]/(A[0][0]||1), b[1]/(A[1][1]||1), b[2]/(A[2][2]||1)];
  };
  const porPlano = nube.modo === 'plano';
  let coef = porPlano ? ajustar(idx) : [0, 0, 0];
  for (let it = 0; porPlano && it < 2; it++) {
    const res = idx.map(i => pos.getY(i) - (coef[0]*pos.getX(i) + coef[1]*pos.getZ(i) + coef[2]));
    const orden = [...res].sort((a,b) => a-b);
    const corte = orden[Math.floor(orden.length * .35)];
    coef = ajustar(idx.filter((i, k) => res[k] > corte));
  }
  const relativa = i => pos.getY(i) - (coef[0]*pos.getX(i) + coef[1]*pos.getZ(i) + coef[2]);

  // rango del color: fijo cuando la pieza lo declara (la huella, para que el hueco mande),
  // y por percentiles en el resto, donde el objeto entero es lo que interesa
  const muestras = idx.map(relativa).sort((a, b) => a - b);
  const ymin = nube.rango_mm ? nube.rango_mm[0] : muestras[Math.floor(muestras.length * .02)];
  const ymax = nube.rango_mm ? nube.rango_mm[1] : muestras[Math.floor(muestras.length * .98)];

  const col = new Float32Array(pos.count * 3);
  for (let i = 0; i < pos.count; i++) {
    const t = Math.max(0, Math.min(1, (relativa(i) - ymin) / (ymax - ymin)));
    const u = t * (RAMPA.length - 1), k = Math.min(RAMPA.length - 2, Math.floor(u)), f = u - k;
    for (let c = 0; c < 3; c++) col[i*3 + c] = RAMPA[k][c] + (RAMPA[k+1][c] - RAMPA[k][c]) * f;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));

  const p = new THREE.Points(g, new THREE.PointsMaterial({
    size: tamano, sizeAttenuation: true, vertexColors: true, color: 0xffffff }));
  p.position.copy(malla.position);
  p.quaternion.copy(malla.quaternion);
  p.scale.copy(malla.scale);
  p.visible = false;
  malla.parent.add(p);                                // mismo padre: hereda la escala del nodo
  return p;
}

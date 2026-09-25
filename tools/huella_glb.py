#!/usr/bin/env python3
"""Reconstruye el GLB de la huella con el relieve horneado en colores de vértice.

El STL no trae ni textura ni UV, así que con luz difusa el modelo se ve como yeso
blanco y la huella desaparece. Aquí se calcula una oclusión de cavidad desde el propio
mapa de altura —hueco = oscuro, cresta = claro— y se escribe en COLOR_0, teñida con
el color del sedimento medido en la foto de la pieza.

    python tools/huella_glb.py            → assets/models/LCDCP-MV-02115.glb (sin comprimir)

Después hay que pasarle Draco:
    npx @gltf-transform/cli optimize <salida> <destino> --compress draco --simplify false
"""
import json
import os
import struct

import cv2
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# el STL original no vive en el proyecto: se indica con MV_ORIGINALES
STL = os.path.join(os.environ.get('MV_ORIGINALES', os.path.join(RAIZ, 'originales', '3D')),
                   'LCDCP-MV-02115.stl')

SEDIMENTO = np.array([82, 51, 32], np.float32) / 255      # mediana de la foto de la pieza
ESCALA_M = 0.001                                          # el STL está en milímetros


def leer_stl(ruta):
    raw = open(ruta, 'rb').read()
    n = struct.unpack_from('<I', raw, 80)[0]
    rec = np.frombuffer(raw, dtype=np.dtype([('n', '<3f4'), ('v', '<3,3f4'), ('a', '<u2')]),
                        count=n, offset=84)
    return rec['v'].reshape(-1, 3).astype(np.float64), rec['n'].astype(np.float64)


def cavidad(vert, lo, hi, mm_px=0.35):
    """Oscurece lo hundido: compara cada vértice contra el promedio de su entorno.

    Dos escalas: una amplia, que hunde la huella entera, y una fina, que marca
    las gravas. Sin esto el modelo se ve plano con cualquier luz difusa.
    """
    W = int((hi[0] - lo[0]) / mm_px)
    H = int((hi[1] - lo[1]) / mm_px)
    xs = np.clip(((vert[:, 0] - lo[0]) / mm_px).astype(int), 0, W - 1)
    ys = np.clip(((vert[:, 1] - lo[1]) / mm_px).astype(int), 0, H - 1)

    alt = np.full((H, W), -np.inf)
    np.maximum.at(alt, (ys, xs), vert[:, 2])
    val = np.isfinite(alt)

    # rellenar huecos con el vecino válido más cercano
    dist, lab = cv2.distanceTransformWithLabels((~val).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    yv, xv = np.nonzero(val)
    orden = np.zeros(lab.max() + 1, np.int64)
    orden[lab[val]] = np.arange(len(yv))
    z = np.where(val, np.where(val, alt, 0), alt[yv[orden[lab]], xv[orden[lab]]]).astype(np.float32)

    ancho = cv2.blur(z, (int(45 / mm_px) | 1, int(45 / mm_px) | 1))    # entorno de 45 mm
    fino = cv2.blur(z, (int(6 / mm_px) | 1, int(6 / mm_px) | 1))       # entorno de 6 mm

    d_ancho = np.clip((z - ancho) / 22 + .5, 0, 1)      # 0 = hundido, 1 = alto
    d_fino = np.clip((z - fino) / 3.5 + .5, 0, 1)
    ao = (.62 * d_ancho + .38 * d_fino)
    ao = .30 + .70 * ao                                  # nunca negro del todo
    return ao[ys, xs].astype(np.float32)


def main():
    vert, nor = leer_stl(STL)
    lo, hi = vert.min(0), vert.max(0)

    uniq, idx = np.unique(vert, axis=0, return_inverse=True)
    acc = np.zeros_like(uniq)
    np.add.at(acc, idx, np.repeat(nor, 3, axis=0))
    ln = np.linalg.norm(acc, axis=1, keepdims=True)
    ln[ln == 0] = 1
    normales = (acc / ln).astype(np.float32)

    ao = cavidad(uniq, lo, hi)
    color = (SEDIMENTO[None, :] * ao[:, None]).astype(np.float32)      # sRGB, vértice a vértice
    print(f'vértices {len(uniq)}  ·  cavidad {ao.min():.2f}–{ao.max():.2f}')

    pos = ((uniq - (lo + hi) / 2) * ESCALA_M).astype(np.float32)       # centrado, en metros
    idx = idx.astype(np.uint32)

    pos_b, nor_b, col_b, idx_b = pos.tobytes(), normales.tobytes(), color.tobytes(), idx.tobytes()
    off = np.cumsum([0, len(pos_b), len(nor_b), len(col_b)])
    blob = pos_b + nor_b + col_b + idx_b
    blob += b'\x00' * ((-len(blob)) % 4)

    gltf = {
        'asset': {'version': '2.0', 'generator': 'huella_glb.py'},
        'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'COLOR_0': 2},
                                    'indices': 3, 'material': 0}]}],
        'materials': [{'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1],
                                                'metallicFactor': 0, 'roughnessFactor': .95},
                       'doubleSided': True, 'name': 'sedimento'}],
        'accessors': [
            {'bufferView': 0, 'componentType': 5126, 'count': len(pos), 'type': 'VEC3',
             'min': pos.min(0).tolist(), 'max': pos.max(0).tolist()},
            {'bufferView': 1, 'componentType': 5126, 'count': len(normales), 'type': 'VEC3'},
            {'bufferView': 2, 'componentType': 5126, 'count': len(color), 'type': 'VEC3'},
            {'bufferView': 3, 'componentType': 5125, 'count': len(idx), 'type': 'SCALAR'}],
        'bufferViews': [
            {'buffer': 0, 'byteOffset': int(off[0]), 'byteLength': len(pos_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[1]), 'byteLength': len(nor_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[2]), 'byteLength': len(col_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[3]), 'byteLength': len(idx_b), 'target': 34963}],
        'buffers': [{'byteLength': len(blob)}],
    }

    js = json.dumps(gltf, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)
    destino = os.path.join(RAIZ, 'assets', 'models', 'LCDCP-MV-02115-color.glb')
    with open(destino, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
    print(f'{destino}  ({os.path.getsize(destino)/1e6:.1f} MB sin comprimir)')


if __name__ == '__main__':
    main()

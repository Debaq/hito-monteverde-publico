#!/usr/bin/env python3
"""Saca el molde de la huella: el volumen que llenaría el hueco, como sólido girable.

Toma el mapa de altura, se queda con lo que encierra el contorno marcado por el equipo,
invierte la depresión en bulto y le pone paredes y base para que sea un cuerpo cerrado.

    python tools/huella_molde.py           → assets/models/huella-molde.glb
"""
import json
import os
import struct

import cv2
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASO_MM = 0.5          # resolución de la malla: a 0.9 mm se perdían los dedos
BASE_MM = 6.0          # espesor de la base bajo el punto más bajo
COLOR = np.array([206, 198, 184], np.float32) / 255    # tono claro de yeso: el café tapaba el detalle


def cargar():
    meta = json.load(open(os.path.join(RAIZ, 'assets/data/huella-altura.json'), encoding='utf-8'))
    cont = json.load(open(os.path.join(RAIZ, 'assets/data/huella-contorno.json'), encoding='utf-8'))
    px = np.asarray(Image.open(os.path.join(RAIZ, 'assets/data/huella-altura.png')).convert('RGB'))
    W, H = meta['px']
    q16 = (px[..., 0].astype(np.uint16) << 8) | px[..., 1]
    z = meta['z_min_mm'] + q16 / 65535 * (meta['z_max_mm'] - meta['z_min_mm'])
    hay = px[..., 2] > 127
    a, b, c = meta['plano']
    yy, xx = np.mgrid[0:H, 0:W]
    prof = np.clip((a * xx + b * yy + c) - z, 0, None)
    prof[~hay] = 0
    return meta, cont, prof.astype(np.float32)


def main():
    meta, cont, prof = cargar()
    mmpx = meta['mm_por_px']
    H, W = prof.shape

    poly = np.array([[p['xy'][0] / mmpx, p['xy'][1] / mmpx] for p in cont['contorno']], np.int32)
    mascara = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mascara, [poly], 1)

    # remuestrear a la resolución del molde
    escala = mmpx / PASO_MM
    nw, nh = int(W * escala), int(H * escala)
    alto = cv2.resize(prof, (nw, nh), interpolation=cv2.INTER_AREA)
    dentro = cv2.resize(mascara * 255, (nw, nh), interpolation=cv2.INTER_AREA) > 127
    # sin suavizado: el detalle fino del molde está a 2-4 mm y se borraba
    alto[~dentro] = 0

    ys, xs = np.nonzero(dentro)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    alto = alto[y0:y1, x0:x1]
    dentro = dentro[y0:y1, x0:x1]
    h, w = alto.shape
    print(f'molde {w}x{h} celdas de {PASO_MM} mm · {dentro.sum()} dentro del contorno')

    # dos capas: la superficie invertida arriba, la base plana abajo
    idx = -np.ones((2, h, w), np.int64)
    pos, nor = [], []
    n = 0
    for capa in (0, 1):
        for j in range(h):
            for i in range(w):
                if not dentro[j, i]:
                    continue
                zz = alto[j, i] if capa == 0 else -BASE_MM
                # glTF usa Y como vertical: la altura del molde va en Y
                pos.append(((x0 + i) * PASO_MM, zz, (y0 + j) * PASO_MM))
                idx[capa, j, i] = n
                n += 1
    pos = np.array(pos, np.float32)

    caras = []
    for capa in (0, 1):
        for j in range(h - 1):
            for i in range(w - 1):
                a_, b_, c_, d_ = idx[capa, j, i], idx[capa, j, i+1], idx[capa, j+1, i+1], idx[capa, j+1, i]
                if min(a_, b_, c_, d_) < 0:
                    continue
                caras += ([a_, b_, c_, a_, c_, d_] if capa == 0 else [a_, c_, b_, a_, d_, c_])

    # paredes: se sigue el borde ordenado de la máscara, no celda por celda
    bordes, _ = cv2.findContours(dentro.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    for borde in bordes:
        pts = [(int(q[0][1]), int(q[0][0])) for q in borde]            # (fila, columna)
        pts = [q for q in pts if idx[0, q[0], q[1]] >= 0]
        for k in range(len(pts)):
            j0, i0 = pts[k]
            j1, i1 = pts[(k + 1) % len(pts)]
            a_, b_ = idx[0, j0, i0], idx[1, j0, i0]
            c_, d_ = idx[0, j1, i1], idx[1, j1, i1]
            caras += [a_, b_, d_, a_, d_, c_]

    # el cambio de ejes invierte la mano: se da vuelta el giro de cada triángulo
    caras = np.array(caras, np.uint32).reshape(-1, 3)[:, ::-1].reshape(-1)
    print(f'vértices {len(pos)} · triángulos {len(caras)//3}')

    # normales por vértice
    tri = caras.reshape(-1, 3)
    v0, v1, v2 = pos[tri[:, 0]], pos[tri[:, 1]], pos[tri[:, 2]]
    fn = np.cross(v1 - v0, v2 - v0)
    nor = np.zeros_like(pos)
    for k in range(3):
        np.add.at(nor, tri[:, k], fn)
    ln = np.linalg.norm(nor, axis=1, keepdims=True); ln[ln == 0] = 1
    nor = (nor / ln).astype(np.float32)

    # sombreado horneado: cada vértice se oscurece según cuánto se hunde respecto de su entorno
    entorno = cv2.blur(alto, (int(8 / PASO_MM) | 1, int(8 / PASO_MM) | 1))
    fino = cv2.blur(alto, (int(2 / PASO_MM) | 1, int(2 / PASO_MM) | 1))
    cav = (np.clip((alto - entorno) / 6 + .5, 0, 1) * .55 +
           np.clip((alto - fino) / 1.2 + .5, 0, 1) * .45)
    cav = (.28 + .72 * cav).astype(np.float32)          # más contraste: el detalle tiene que leerse

    col = np.zeros((len(pos), 3), np.float32)
    for capa in (0, 1):
        for j in range(h):
            for i in range(w):
                k = idx[capa, j, i]
                if k < 0:
                    continue
                col[k] = COLOR * (cav[j, i] if capa == 0 else .5)   # la base, más apagada

    # centrar y pasar a metros
    pos = ((pos - pos.mean(0)) * 0.001).astype(np.float32)

    pos_b, nor_b, col_b, idx_b = pos.tobytes(), nor.tobytes(), col.tobytes(), caras.tobytes()
    off = np.cumsum([0, len(pos_b), len(nor_b), len(col_b)])
    blob = pos_b + nor_b + col_b + idx_b
    blob += b'\x00' * ((-len(blob)) % 4)

    gltf = {
        'asset': {'version': '2.0', 'generator': 'huella_molde.py'},
        'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'mesh': 0}],
        'meshes': [{'primitives': [{'attributes': {'POSITION': 0, 'NORMAL': 1, 'COLOR_0': 2},
                                    'indices': 3, 'material': 0}]}],
        'materials': [{'name': 'molde', 'doubleSided': True,
                       'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1],
                                                'metallicFactor': 0, 'roughnessFactor': .85}}],
        'accessors': [
            {'bufferView': 0, 'componentType': 5126, 'count': len(pos), 'type': 'VEC3',
             'min': pos.min(0).tolist(), 'max': pos.max(0).tolist()},
            {'bufferView': 1, 'componentType': 5126, 'count': len(nor), 'type': 'VEC3'},
            {'bufferView': 2, 'componentType': 5126, 'count': len(col), 'type': 'VEC3'},
            {'bufferView': 3, 'componentType': 5125, 'count': len(caras), 'type': 'SCALAR'}],
        'bufferViews': [
            {'buffer': 0, 'byteOffset': int(off[0]), 'byteLength': len(pos_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[1]), 'byteLength': len(nor_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[2]), 'byteLength': len(col_b), 'target': 34962},
            {'buffer': 0, 'byteOffset': int(off[3]), 'byteLength': len(idx_b), 'target': 34963}],
        'buffers': [{'byteLength': len(blob)}],
    }
    js = json.dumps(gltf, separators=(',', ':')).encode()
    js += b' ' * ((-len(js)) % 4)

    destino = os.path.join(RAIZ, 'assets', 'models', 'huella-molde.glb')
    with open(destino, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob)))
        f.write(struct.pack('<II', len(js), 0x4E4F534A)); f.write(js)
        f.write(struct.pack('<II', len(blob), 0x004E4942)); f.write(blob)
    print(f'{destino}  ({os.path.getsize(destino)/1e6:.1f} MB)')


if __name__ == '__main__':
    main()

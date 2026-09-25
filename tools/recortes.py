#!/usr/bin/env python3
"""Recorta cada pieza de su fondo blanco y calcula su escala real.

Sale un webp con transparencia por pieza y assets/data/recortes.json con los
mm por píxel, que es lo que permite mostrarlas a tamaño real en AR.

La regla de escala del catálogo se descarta por su rojo saturado: la pieza
ronda el 0.4 % de rojo vivo y la regla el 31 %.
"""
import json
import os

import cv2
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTRADA = os.path.join(RAIZ, 'assets', 'images')
SALIDA = os.path.join(ENTRADA, 'recortes')
LADO_MAX = 2000


def segmentar(rgb):
    """Máscara de la pieza, sin fondo ni regla de escala."""
    h, w = rgb.shape[:2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    sat, val, hue = hsv[..., 1], hsv[..., 2], hsv[..., 0]

    # umbral estricto: deja fuera la sombra de estudio (gris claro, poco saturada)
    obj = ((val < 200) | (sat > 55)).astype(np.uint8)
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
    obj = cv2.morphologyEx(obj, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    obj = cv2.dilate(obj, np.ones((3, 3), np.uint8))          # recupera el borde real
    obj = cv2.morphologyEx(obj, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))

    n, lab, stats, _ = cv2.connectedComponentsWithStats(obj, 8)
    piezas = []
    for i in range(1, n):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < h * w * 0.002:
            continue
        m = lab == i
        rojo_vivo = float(((sat[m] > 120) & (val[m] > 110) &
                           ((hue[m] < 12) | (hue[m] > 168))).mean())
        if rojo_vivo > 0.05:            # es la regla de escala
            continue
        piezas.append((area, i))
    if not piezas:
        return None
    piezas.sort(reverse=True)
    mayor = piezas[0][0]
    keep = [i for a, i in piezas if a > mayor * 0.12]   # piezas fragmentadas en varios trozos
    return np.isin(lab, keep).astype(np.uint8) * 255


def recortar(codigo, dims):
    origen = os.path.join(ENTRADA, f'{codigo}.webp')
    if not os.path.exists(origen):
        return None
    rgb = np.asarray(Image.open(origen).convert('RGB'))
    alpha = segmentar(rgb)
    if alpha is None:
        return None

    # erosionar antes de difuminar elimina el fleco blanco del fondo
    alpha = cv2.erode(alpha, np.ones((3, 3), np.uint8), iterations=2)
    alpha = cv2.GaussianBlur(alpha, (3, 3), 0)
    ys, xs = np.where(alpha > 10)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    rec = np.dstack([rgb, alpha])[y0:y1, x0:x1]

    esc = min(1.0, LADO_MAX / max(rec.shape[:2]))
    if esc < 1:
        rec = cv2.resize(rec, (int(rec.shape[1] * esc), int(rec.shape[0] * esc)),
                         interpolation=cv2.INTER_AREA)

    os.makedirs(SALIDA, exist_ok=True)
    destino = os.path.join(SALIDA, f'{codigo}.webp')
    Image.fromarray(rec).save(destino, quality=88, method=6)

    alto, ancho = rec.shape[:2]
    info = {'archivo': f'assets/images/recortes/{codigo}.webp', 'px': [ancho, alto]}
    largo_cm = (dims or {}).get('largo')
    if largo_cm:                        # el lado mayor del recorte es el largo de la ficha
        info['mm_por_px'] = round(largo_cm * 10 / max(ancho, alto), 5)
        info['tamano_real_mm'] = [round(ancho * largo_cm * 10 / max(ancho, alto), 1),
                                  round(alto * largo_cm * 10 / max(ancho, alto), 1)]
    return info


def main():
    cat = json.load(open(os.path.join(RAIZ, 'assets', 'data', 'catalogo.json'), encoding='utf-8'))
    salida = {}
    for p in cat['piezas']:
        info = recortar(p['codigo'], p.get('dimensiones'))
        if info:
            salida[p['codigo']] = info
            real = info.get('tamano_real_mm')
            print(f"{p['codigo']:<16}{info['px'][0]:>5}x{info['px'][1]:<5}"
                  f"{'  ' + str(real[0]) + ' x ' + str(real[1]) + ' mm reales' if real else '  sin medidas'}")
        else:
            print(f"{p['codigo']:<16}no se pudo separar del fondo")

    with open(os.path.join(RAIZ, 'assets', 'data', 'recortes.json'), 'w', encoding='utf-8') as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)
    print(f'\n{len(salida)} recortes')


if __name__ == '__main__':
    main()

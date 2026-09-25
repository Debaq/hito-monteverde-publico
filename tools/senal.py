#!/usr/bin/env python3
"""Señalética de pared para cortar en plóter: la flecha de INICIO y la palabra QR.

    python tools/senal.py                      medidas por defecto
    python tools/senal.py ancho=700 alto=500   la flecha más grande
    python tools/senal.py lado=izquierda       la flecha dobla por la izquierda
    python tools/senal.py qr=150               la palabra QR de 150 mm de alto

Medidas en milímetros:

    ancho    largo del tramo horizontal, esquina incluida            (560)
    alto     alto total, de arriba hasta la punta                     (420)
    grosor   grosor de la barra                                       (90)
    punta    ancho de la punta de la flecha                           (200)
    lado     derecha | izquierda: hacia dónde dobla hacia abajo       (derecha)
    qr       alto de las mayúsculas de QR                             (120)

La flecha es una barra horizontal que dobla en ángulo recto hacia abajo y termina en
punta. INICIO va calado en el tramo horizontal: se corta en vinilo negro y las letras
se pelan, así que la palabra queda del color de la pared. Los centros de la O quedan
negros, como islas: salen con el papel de transferencia sin problema.

Las letras van como contornos, no como texto, porque el plóter no conoce fuentes. La
tipografía es la del sitio, Plus Jakarta Sans, en extra negrita. Es variable, y las
variables arman letras como la N, la Q o la R con trazos que se montan: sin unirlos,
el plóter corta líneas de más por dentro de la letra y el relleno sale con manchas.
Para unirlos hace falta skia-pathops:

    pip install skia-pathops fonttools brotli

Salida en assets/impresos/vinilo/, de cada pieza:

    ….svg   para el plóter y para ver cómo queda (el negro relleno)
    ….dxf   lo mismo en DXF R12, en mm, para Silhouette Studio básico
"""
import os
import sys

try:
    import pathops
except ImportError:
    sys.exit('falta skia-pathops, que une los trazos de las letras:\n'
             '    pip install skia-pathops fonttools brotli')
from fontTools.pens.basePen import BasePen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'assets', 'impresos', 'vinilo')
FUENTE = os.path.join(RAIZ, 'assets', 'fonts', 'plus-jakarta-sans-latin.woff2')
PESO = 800                        # extra negrita: se lee de lejos y las letras no salen finas

POR_DEFECTO = {'ancho': 560, 'alto': 420, 'grosor': 90, 'punta': 200, 'lado': 'derecha', 'qr': 120}
ALTO_LETRA = .52                  # mayúsculas de INICIO, como fracción del grosor de la barra
ESPACIADO = .06                   # aire entre letras, como fracción del alto de mayúscula
LARGO_PUNTA = .72                 # largo de la punta, como fracción de su ancho: se lee firme
PASOS_CURVA = 12                  # segmentos por curva al pasarla a DXF


# ---------- letras
def fuente():
    f = TTFont(FUENTE)
    if 'fvar' in f:
        f = instantiateVariableFont(f, {'wght': PESO})
    return f


def palabra(f, texto, alto_mayus, x=0, y_base=0):
    """Las letras de `texto` como un solo trazo en mm, ya unidas, y su ancho.

    (x, y_base) es el comienzo de la línea de base, en coordenadas de SVG: la y crece
    hacia abajo.
    """
    cmap, gs = f.getBestCmap(), f.getGlyphSet()
    k = alto_mayus / f['OS/2'].sCapHeight
    aire = ESPACIADO * f['OS/2'].sCapHeight
    trazo, cursor = pathops.Path(), 0
    for letra in texto:
        nombre = cmap[ord(letra)]
        m = (k, 0, 0, -k, x + cursor * k, y_base)          # unidades de fuente -> mm, y hacia abajo
        gs[nombre].draw(TransformPen(trazo.getPen(), m))
        cursor += gs[nombre].width + aire
    trazo.simplify()                               # une los trazos que se montan
    return trazo, (cursor - aire) * k


# ---------- flecha
def flecha(ancho, alto, grosor, punta):
    """Contorno de la flecha que dobla por la derecha, en mm, desde arriba a la izquierda."""
    largo = punta * LARGO_PUNTA
    c = ancho - grosor / 2                         # eje de la barra vertical
    return [(0, 0), (ancho, 0), (ancho, alto - largo),
            (c + punta / 2, alto - largo), (c, alto), (c - punta / 2, alto - largo),
            (ancho - grosor, alto - largo), (ancho - grosor, grosor), (0, grosor)]


def poligono(pts):
    trazo = pathops.Path()
    pen = trazo.getPen()
    pen.moveTo(pts[0])
    for p in pts[1:]:
        pen.lineTo(p)
    pen.closePath()
    return trazo


# ---------- salida
class Polilineas(BasePen):
    """Aplana un trazo en polilíneas cerradas, que es lo que lleva el DXF R12."""

    def __init__(self):
        super().__init__(None)
        self.contornos, self.actual = [], None

    def _moveTo(self, p):
        self.actual = [p]

    def _lineTo(self, p):
        self.actual.append(p)

    def _curveToOne(self, p1, p2, p3):
        p0 = self.actual[-1]
        for i in range(1, PASOS_CURVA + 1):
            t = i / PASOS_CURVA
            u = 1 - t
            self.actual.append(tuple(u**3 * a + 3 * u*u * t * b + 3 * u * t*t * c + t**3 * d
                                     for a, b, c, d in zip(p0, p1, p2, p3)))

    def _qCurveToOne(self, p1, p2):
        p0 = self.actual[-1]
        for i in range(1, PASOS_CURVA + 1):
            t = i / PASOS_CURVA
            u = 1 - t
            self.actual.append(tuple(u*u * a + 2 * u * t * b + t*t * c for a, b, c in zip(p0, p1, p2)))

    def _closePath(self):
        if self.actual:
            self.contornos.append(self.actual)
        self.actual = None

    _endPath = _closePath


def guardar(trazo, base, titulo, nota):
    """SVG y DXF de una pieza, con el origen en su esquina superior izquierda."""
    x0, y0, x1, y1 = trazo.bounds
    w, h = x1 - x0, y1 - y0
    nombre = f'{base}-{w:.0f}x{h:.0f}mm'

    svg = SVGPathPen(None)
    trazo.draw(svg)
    with open(os.path.join(SALIDA, nombre + '.svg'), 'w', encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- {titulo}. Medidas reales: {w:.0f} x {h:.0f} mm. Lo negro es lo que queda pegado. -->
<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}mm" height="{h:.2f}mm" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}">
  <path d="{svg.getCommands()}" fill="#000" fill-rule="evenodd" stroke="none"/>
</svg>
''')

    # DXF R12 en mm, con la y hacia arriba como la quiere el DXF
    pl = Polilineas()
    trazo.draw(pl)
    ln = ['0', 'SECTION', '2', 'ENTITIES']
    for pts in pl.contornos:
        ln += ['0', 'POLYLINE', '8', 'CORTE', '66', '1', '70', '1',
               '10', '0.0', '20', '0.0', '30', '0.0']
        for x, y in pts:
            ln += ['0', 'VERTEX', '8', 'CORTE', '10', f'{x - x0:.4f}', '20', f'{y1 - y:.4f}', '30', '0.0']
        ln += ['0', 'SEQEND', '8', 'CORTE']
    ln += ['0', 'ENDSEC', '0', 'EOF']
    with open(os.path.join(SALIDA, nombre + '.dxf'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(ln) + '\n')
    return nombre, w, h, len(pl.contornos), nota


def pedidos(args):
    p = dict(POR_DEFECTO)
    for a in args:
        if '=' not in a:
            sys.exit(f'no entiendo "{a}": se escribe nombre=valor, por ejemplo ancho=600')
        k, v = a.split('=', 1)
        if k not in p:
            sys.exit(f'"{k}" no es una medida: {", ".join(POR_DEFECTO)}')
        p[k] = v if k == 'lado' else float(v)
    if p['lado'] not in ('derecha', 'izquierda'):
        sys.exit('lado es derecha o izquierda')
    if p['punta'] <= p['grosor']:
        sys.exit('la punta tiene que ser más ancha que la barra')
    if p['alto'] < p['grosor'] + p['punta'] * LARGO_PUNTA + 20:
        sys.exit('no hay alto suficiente para la barra vertical y la punta')
    return p


def main():
    p = pedidos(sys.argv[1:])
    os.makedirs(SALIDA, exist_ok=True)
    f = fuente()
    hechos = []

    # --- flecha con INICIO calado: las letras se restan de la flecha
    g = p['grosor']
    pts = flecha(p['ancho'], p['alto'], g, p['punta'])
    if p['lado'] == 'izquierda':
        pts = [(p['ancho'] - x, y) for x, y in pts]
    tramo = p['ancho'] - g                         # la parte recta del horizontal, sin la esquina
    margen = g * .45
    alto_mayus = g * ALTO_LETRA
    alto_mayus *= min(1, (tramo - 2 * margen) / palabra(f, 'INICIO', alto_mayus)[1])   # que quepa
    ancho_txt = palabra(f, 'INICIO', alto_mayus)[1]
    x_txt = (g if p['lado'] == 'izquierda' else 0) + (tramo - ancho_txt) / 2
    letras, _ = palabra(f, 'INICIO', alto_mayus, x_txt, g / 2 + alto_mayus / 2)
    pieza = pathops.op(poligono(pts), letras, pathops.PathOp.DIFFERENCE)
    hechos.append(guardar(pieza, f"senal-inicio-flecha-{p['lado']}", 'Flecha de INICIO, INICIO calado',
                          f'INICIO con mayúsculas de {alto_mayus:.0f} mm'))

    # --- la palabra QR, en negro
    letras, _ = palabra(f, 'QR', p['qr'], 0, p['qr'])
    hechos.append(guardar(letras, f"senal-qr-{p['qr']:.0f}", 'La palabra QR',
                          f'mayúsculas de {p["qr"]:.0f} mm; la cola de la Q baja un poco más'))

    for nombre, w, h, n, nota in hechos:
        print(f'{nombre}.svg / .dxf   {w:.0f} x {h:.0f} mm   {n} contornos de corte   {nota}')


if __name__ == '__main__':
    main()

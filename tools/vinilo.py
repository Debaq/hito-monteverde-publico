#!/usr/bin/env python3
"""Marcadores ArUco en SVG para cortar en plóter y pegar en el suelo.

    python tools/vinilo.py LCDCP-MV-02115            400 mm de marcador
    python tools/vinilo.py LCDCP-MV-02115 600        el tamaño que se quiera
    python tools/vinilo.py LCDCP-MV-02115 300 probar  sólo el archivo, sin anotar el tamaño
    python tools/vinilo.py LCDCP-MV-02115 360 silencio=1.5   menos blanco alrededor

Salida en assets/impresos/vinilo/. De cada marcador salen tres archivos:

    …-marca.svg   SOLO el negro, al tamaño justo: es lo que va al plóter
    ….svg         las dos capas juntas, para ver el montaje y medir el blanco
    ….dxf         lo mismo en DXF, para Silhouette Studio básico

El blanco se corta a mano: es un cuadrado liso y no necesita máquina. Lo único que
tiene que cumplir es dejar margen blanco alrededor del negro (la zona de silencio).

Van en dos capas porque el marcador necesita blanco alrededor y debajo: sobre un
suelo de color, o de hormigón manchado, la lectura se cae. Si el suelo ya es liso y
claro se puede cortar sólo la capa negra, bajo el propio riesgo.

Los módulos negros que se tocan salen unidos en un solo contorno, no como celdas
sueltas: un plóter que corta cada celda por separado deja el vinilo en pedacitos y
además repasa dos veces cada línea interior.

El tamaño real queda anotado en assets/data/marcadores.json (bloque `suelo`), que es
de donde ar.html saca la escala para estimar la pose. Un marcador de 400 mm leído
como si midiera 52 pone la pieza a un octavo de la distancia que corresponde.
"""
import json
import os
import sys

import cv2
import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, 'tools'))

from impresos import DICC, cargar_catalogo, asignar_ids          # noqa: E402

SALIDA = os.path.join(RAIZ, 'assets', 'impresos', 'vinilo')
DATOS = os.path.join(RAIZ, 'assets', 'data', 'marcadores.json')

MODULOS = 6                  # 4x4 de datos más el borde negro de un módulo
SILENCIO = 2                 # módulos blancos alrededor: uno es el mínimo, dos van sobrados
IDS_DICC = 100               # DICT_4X4_100
LADO_POR_DEFECTO = 400       # mm


def silencio_pedido(args):
    """Módulos de blanco alrededor del marcador, si se piden por línea de órdenes.

    Dos es lo cómodo, uno es el mínimo que admite ArUco. Se baja cuando la hoja blanca
    no cabe en el ancho de corte del plóter.
    """
    for a in args:
        if a.startswith('silencio='):
            return max(1.0, float(a.split('=')[1]))
    return SILENCIO


def _bits(marker_id):
    """Los 16 módulos de datos del marcador, sin el borde negro."""
    img = DICC.generateImageMarker(marker_id, MODULOS, borderBits=1)
    return (img[1:MODULOS - 1, 1:MODULOS - 1] > 0).astype(int)


def distancia(a, b):
    """Módulos en que se diferencian dos marcadores, en la rotación más parecida.

    Es lo que separa un id de otro cuando la lectura sale sucia: en un 4x4 hay 16
    módulos y lo habitual en este diccionario es que dos ids difieran en 4. Cuanto más
    alto, más tiene que equivocarse el detector para devolver la pieza que no es.
    """
    A, B = _bits(a), _bits(b)
    return min(int(np.sum(A != np.rot90(B, k))) for k in range(4))


def elegir_id(mapa, codigo):
    """El id libre que más se diferencia de los que ya están en uso.

    Antes se tomaba un número fijo más la posición de la pieza. Eso daba ids que por
    casualidad quedaban a 3 módulos de otro ya impreso, que es justo como se acaba
    mostrando una pieza equivocada.
    """
    suelo = mapa.get('suelo', {})
    if codigo in suelo:
        return suelo[codigo]['id']
    usados = set(mapa.get('placas', {}).values()) | {v['id'] for v in suelo.values()}
    for info in mapa.get('cubos', {}).values():
        usados |= set(info['caras'].values())
    libres = [i for i in range(IDS_DICC) if i not in usados]
    return max(libres, key=lambda i: (min(distancia(i, u) for u in usados), i))


def matriz(marker_id):
    """El marcador como matriz de 0 y 1 (1 = negro), un valor por módulo."""
    img = DICC.generateImageMarker(marker_id, MODULOS, borderBits=1)
    return (img == 0).astype(np.uint8)


def contornos(m, paso):
    """Los módulos negros como polígonos en milímetros, agujeros incluidos.

    Se trabaja sobre la matriz ampliada para que los contornos caigan en los bordes de
    cada módulo y no en su centro, que es donde los deja findContours.
    """
    grande = np.kron(m, np.ones((100, 100), np.uint8))       # 100 px por módulo
    cs, jerarquia = cv2.findContours(grande, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    salida = []
    for c in cs:
        pts = cv2.approxPolyDP(c, 2, True).reshape(-1, 2).astype(float)
        # de centro de píxel a borde de módulo: se redondea al múltiplo de 100
        pts = np.round(pts / 100) * paso
        salida.append(pts)
    return salida, jerarquia


def svg(marker_id, lado_mm, ruta, silencio=SILENCIO):
    m = matriz(marker_id)
    paso = lado_mm / MODULOS
    borde = silencio * paso
    base = lado_mm + 2 * borde

    caminos, _ = contornos(m, paso)
    d = []
    for pts in caminos:
        pts = pts + borde                                     # el marcador va centrado en la base
        d.append('M ' + ' L '.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z')

    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!-- Marcador ArUco {DICC_NOMBRE} id {marker_id} · marcador {lado_mm:g} mm ·
     hoja {base:g} x {base:g} mm · módulo {paso:.2f} mm
     Cortar "base-blanca" en vinilo blanco y "marca-negra" en negro, y pegar la negra
     centrada sobre la blanca. Imprescindible: no reescalar el archivo. -->
<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape"
     width="{base:g}mm" height="{base:g}mm" viewBox="0 0 {base:g} {base:g}">
  <title>Monte Verde · marcador de suelo id {marker_id} · {lado_mm:g} mm</title>
  <g id="base-blanca" inkscape:groupmode="layer" inkscape:label="1 base blanca">
    <rect x="0" y="0" width="{base:g}" height="{base:g}"
          fill="#ffffff" stroke="#000000" stroke-width="0.2"/>
  </g>
  <g id="marca-negra" inkscape:groupmode="layer" inkscape:label="2 marca negra">
    <path fill="#000000" fill-rule="evenodd" stroke="none"
          d="{' '.join(d)}"/>
  </g>
</svg>
''')
    return base


DICC_NOMBRE = 'DICT_4X4_100'


def svg_marca(marker_id, lado_mm, ruta):
    """Sólo el negro, en un lienzo del tamaño del marcador: lo que se manda a cortar.

    Aparte del archivo con las dos capas, porque en el plóter no hay que cortar el
    blanco y una capa oculta que se muestra sin querer arruina una plancha de vinilo.
    """
    paso = lado_mm / MODULOS
    caminos, _ = contornos(matriz(marker_id), paso)
    d = ['M ' + ' L '.join(f'{x:.3f},{y:.3f}' for x, y in pts) + ' Z' for pts in caminos]
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- Marcador ArUco {DICC_NOMBRE} id {marker_id} · {lado_mm:g} x {lado_mm:g} mm ·
     módulo {paso:.2f} mm · cortar en vinilo negro mate, sin reescalar.
     Va pegado sobre blanco, dejando al menos {SILENCIO * paso:.0f} mm de blanco por lado. -->
<svg xmlns="http://www.w3.org/2000/svg" width="{lado_mm:g}mm" height="{lado_mm:g}mm"
     viewBox="0 0 {lado_mm:g} {lado_mm:g}">
  <title>Monte Verde · marcador de suelo id {marker_id} · {lado_mm:g} mm</title>
  <path fill="#000000" fill-rule="evenodd" stroke="none" d="{' '.join(d)}"/>
</svg>
""")


def dxf(marker_id, lado_mm, ruta, silencio=SILENCIO):
    """El mismo corte en DXF R12, en milímetros.

    Silhouette Studio sólo importa SVG con la Designer Edition; DXF lo lee la versión
    básica. Se escribe a mano y no con el exportador de Inkscape porque ese saca las
    coordenadas en píxeles de usuario y el dibujo entra con la escala cambiada.
    """
    paso = lado_mm / MODULOS
    borde = silencio * paso
    base = lado_mm + 2 * borde
    caminos, _ = contornos(matriz(marker_id), paso)

    piezas = [('BASE', [(0, 0), (base, 0), (base, base), (0, base)])]
    for pts in caminos:
        piezas.append(('MARCA', [(x + borde, base - (y + borde)) for x, y in pts]))

    ln = ['0', 'SECTION', '2', 'ENTITIES']
    for capa, pts in piezas:
        ln += ['0', 'POLYLINE', '8', capa, '66', '1', '70', '1',
               '10', '0.0', '20', '0.0', '30', '0.0']
        for x, y in pts:
            ln += ['0', 'VERTEX', '8', capa, '10', f'{x:.4f}', '20', f'{y:.4f}', '30', '0.0']
        ln += ['0', 'SEQEND', '8', capa]
    ln += ['0', 'ENDSEC', '0', 'EOF']
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write('\n'.join(ln) + '\n')


def registrar(codigo, marker_id, lado_mm):
    """Deja el tamaño real anotado, que es lo que el visor necesita para la pose."""
    with open(DATOS, encoding='utf-8') as f:
        mapa = json.load(f)
    mapa.setdefault('suelo', {})[codigo] = {'id': marker_id, 'lado_mm': lado_mm}
    with open(DATOS, 'w', encoding='utf-8') as f:
        json.dump(mapa, f, ensure_ascii=False, indent=2)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    codigo = sys.argv[1]
    lado = float(sys.argv[2]) if len(sys.argv) > 2 else LADO_POR_DEFECTO
    # `probar` saca el SVG sin tocar marcadores.json: para comparar tamaños antes de
    # decidir cuál se corta. El tamaño anotado tiene que ser el del vinilo que se pega,
    # y sólo puede haber uno por pieza.
    probar = 'probar' in sys.argv[3:]
    silencio = silencio_pedido(sys.argv[3:])

    piezas = cargar_catalogo()
    if not any(p['codigo'] == codigo for p in piezas):
        print(f'{codigo} no está en el catálogo')
        return

    with open(DATOS, encoding='utf-8') as f:
        mapa = json.load(f)
    marker_id = elegir_id(mapa, codigo)

    os.makedirs(SALIDA, exist_ok=True)
    nombre = f'vinilo-{codigo}-id{marker_id}-{lado:g}mm'
    if silencio != SILENCIO:                  # el blanco cambia, el marcador no
        nombre += f'-silencio{silencio:g}'
    ruta = os.path.join(SALIDA, nombre + '.svg')
    base = svg(marker_id, lado, ruta, silencio)
    svg_marca(marker_id, lado, os.path.join(SALIDA, nombre + '-marca.svg'))
    dxf(marker_id, lado, os.path.join(SALIDA, nombre + '.dxf'), silencio)
    if not probar:
        registrar(codigo, marker_id, lado)

    print(os.path.relpath(os.path.join(SALIDA, nombre + '-marca.svg'), RAIZ), ' ← al plóter')
    print(os.path.relpath(ruta, RAIZ))
    print(os.path.relpath(os.path.join(SALIDA, nombre + '.dxf'), RAIZ))
    print(f'negro {lado:g} x {lado:g} mm · blanco {base:g} x {base:g} mm · módulo {lado/MODULOS:.1f} mm')
    print(f'id {marker_id}, anotado en {os.path.relpath(DATOS, RAIZ)}' if not probar
          else f'id {marker_id} · sin anotar (prueba)')


if __name__ == '__main__':
    main()

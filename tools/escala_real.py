#!/usr/bin/env python3
"""Devuelve a los GLB su tamaño real, en metros (la unidad de glTF).

Sin esto, "ver en tu espacio" muestra la pieza del tamaño que quedó al exportar:
el guijarro de 2.3 cm aparece como una roca de 2 m. La escala sale de las medidas
de la ficha; para la huella, del bbox del STL original, que venía en milímetros.

Toca sólo el chunk JSON del GLB: la geometría Draco queda intacta.
"""
import json
import os
import struct
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# piezas sin medidas en la ficha: largo real en metros, medido aparte
LARGOS_EXTRA = {
    'LCDCP-MV-02115': 0.32971,      # bbox del STL original: 329.71 mm
}


def leer_glb(ruta):
    with open(ruta, 'rb') as f:
        datos = f.read()
    magia, version, total = struct.unpack_from('<III', datos, 0)
    assert magia == 0x46546C67, f'{ruta} no es un GLB'
    off, trozos = 12, []
    while off < total:
        largo, tipo = struct.unpack_from('<II', datos, off)
        trozos.append((tipo, datos[off + 8: off + 8 + largo]))
        off += 8 + largo
    return trozos


def escribir_glb(ruta, trozos):
    cuerpo = b''
    for tipo, datos in trozos:
        relleno = b' ' if tipo == 0x4E4F534A else b'\x00'
        datos = datos + relleno * ((-len(datos)) % 4)
        cuerpo += struct.pack('<II', len(datos), tipo) + datos
    with open(ruta, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + len(cuerpo)) + cuerpo)


def extension_actual(gltf):
    """Lado mayor del bbox, leído de los accessors de POSITION."""
    ext = 0
    for malla in gltf.get('meshes', []):
        for prim in malla.get('primitives', []):
            i = prim.get('attributes', {}).get('POSITION')
            if i is None:
                continue
            acc = gltf['accessors'][i]
            if 'min' in acc and 'max' in acc:
                ext = max(ext, max(hi - lo for lo, hi in zip(acc['min'], acc['max'])))
    return ext


def reescalar(ruta, largo_real_m):
    trozos = leer_glb(ruta)
    idx = next(i for i, (t, _) in enumerate(trozos) if t == 0x4E4F534A)
    gltf = json.loads(trozos[idx][1].decode('utf-8'))

    actual = extension_actual(gltf)
    if not actual:
        return None
    factor = largo_real_m / actual

    # un nodo raíz nuevo sostiene la escala: no toca las transformaciones existentes
    escena = gltf['scenes'][gltf.get('scene', 0)]
    gltf['nodes'].append({'name': 'escala_real',
                          'scale': [factor, factor, factor],
                          'children': list(escena['nodes'])})
    escena['nodes'] = [len(gltf['nodes']) - 1]

    trozos[idx] = (0x4E4F534A, json.dumps(gltf, separators=(',', ':')).encode('utf-8'))
    escribir_glb(ruta, trozos)
    return actual, factor, actual * factor


def main():
    cat = json.load(open(os.path.join(RAIZ, 'assets', 'data', 'catalogo.json'), encoding='utf-8'))
    solo = sys.argv[1] if len(sys.argv) > 1 else None

    for p in cat['piezas']:
        if solo and p['codigo'] != solo:
            continue
        if not p['media'].get('modelo'):
            continue
        largo_cm = (p.get('dimensiones') or {}).get('largo')
        largo_m = largo_cm / 100 if largo_cm else LARGOS_EXTRA.get(p['codigo'])
        if not largo_m:
            print(f"{p['codigo']:<16}sin medidas: no se puede escalar")
            continue

        for clave in ('modelo', 'modelo_movil'):
            ruta = os.path.join(RAIZ, p['media'][clave])
            r = reescalar(ruta, largo_m)
            if r:
                actual, factor, final = r
                print(f"{p['codigo']:<16}{clave:<14}{actual:8.3f} → {final:.3f} m "
                      f"(×{factor:.4f})")


if __name__ == '__main__':
    main()

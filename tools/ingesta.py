#!/usr/bin/env python3
"""Recibe modelos 3D nuevos y los deja listos para el sitio, sin intervención manual.

    python tools/ingesta.py                      procesa la carpeta de MV_ORIGINALES
    python tools/ingesta.py archivo.glb          procesa uno solo
    python tools/ingesta.py --revisar            sólo informa qué haría, no escribe nada

De cada archivo se detecta y corrige lo que los exportadores suelen dejar mal:

  · unidades      milímetros, centímetros o metros, deducidas del tamaño de la pieza
                  y contrastadas con las dimensiones de la ficha cuando existen
  · eje vertical  si la altura quedó en Z (Blender) se rota para que quede en Y
  · escala real   se ajusta al largo que declara la ficha; sin ficha, a lo detectado
  · centrado      la pieza queda centrada en su propio origen

Después comprime con Draco, arma la versión móvil y actualiza catalogo.json.
El nombre del archivo tiene que empezar con el código de la pieza: LCDCP-MV-00008*.glb
"""
import json
import os
import re
import shutil
import struct
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Los originales no viven en el proyecto. Se indica la carpeta con MV_ORIGINALES,
# o se pasan los .glb sueltos como argumento.
ENTRADA = os.environ.get('MV_ORIGINALES', os.path.join(RAIZ, 'originales', '3D'))
MODELOS = os.path.join(RAIZ, 'assets', 'models')
CLI = ['npx', '--yes', '@gltf-transform/cli@4.5.0']
# los nombres llegan con y sin el guion antes del número: se aceptan los dos
CODIGO = re.compile(r'LCDCP[-_ ]?MV[-_ ]?(\d+)', re.I)


# ---------------------------------------------------------------- GLB crudo
def leer_glb(ruta):
    raw = open(ruta, 'rb').read()
    total = struct.unpack_from('<I', raw, 8)[0]
    off, js, bin_ = 12, None, b''
    while off < total:
        largo, tipo = struct.unpack_from('<II', raw, off)
        datos = raw[off + 8: off + 8 + largo]
        if tipo == 0x4E4F534A:
            js = json.loads(datos.decode('utf-8'))
        else:
            bin_ = datos
        off += 8 + largo
    return js, bin_


def escribir_glb(ruta, js, bin_):
    jsb = json.dumps(js, separators=(',', ':')).encode()
    jsb += b' ' * ((-len(jsb)) % 4)
    bb = bin_ + b'\x00' * ((-len(bin_)) % 4)
    cuerpo = (struct.pack('<II', len(jsb), 0x4E4F534A) + jsb +
              struct.pack('<II', len(bb), 0x004E4942) + bb)
    with open(ruta, 'wb') as f:
        f.write(struct.pack('<III', 0x46546C67, 2, 12 + len(cuerpo)) + cuerpo)


def extension(js):
    """Tamaño de la pieza según los accessors de POSITION, sin decodificar nada."""
    lo = [float('inf')] * 3
    hi = [float('-inf')] * 3
    for malla in js.get('meshes', []):
        for prim in malla.get('primitives', []):
            i = prim.get('attributes', {}).get('POSITION')
            if i is None:
                continue
            acc = js['accessors'][i]
            if 'min' not in acc:
                continue
            for k in range(3):
                lo[k] = min(lo[k], acc['min'][k])
                hi[k] = max(hi[k], acc['max'][k])
    return lo, [hi[k] - lo[k] for k in range(3)]


def unidades(tam, largo_ficha_cm):
    """Factor a metros, explicación, y aviso cuando el dato no es confiable.

    Un archivo normalizado (la pieza mide ~1-2 unidades) no tiene unidad posible: ahí
    sólo sirve el largo de la ficha. Un archivo con unidades reales sí las tiene, y si
    discrepa con la ficha **no se lo estira**: se respeta el escaneo y se avisa, porque
    la ficha puede estar midiendo otro eje o la pieza completa antes de recortarla.
    """
    mayor = max(tam)
    normalizado = mayor < 10
    objetivo = largo_ficha_cm / 100 if largo_ficha_cm else None

    if normalizado:
        if objetivo:
            return objetivo / mayor, f'normalizado: escalado al largo de ficha ({largo_ficha_cm} cm)', None
        return 1.0, 'normalizado y sin medidas en la ficha', 'no hay con qué fijar la escala'

    err, f, n = min((abs(mayor * f - objetivo) / objetivo, f, n) if objetivo else (0, f, n)
                    for f, n in ((0.001, 'mm'), (0.01, 'cm'), (1.0, 'm')))
    if not objetivo:
        f, n = (0.001, 'mm') if mayor > 20 else ((0.01, 'cm') if mayor > 3 else (1.0, 'm'))
        return f, f'{n} (deducido del tamaño)', 'la ficha no trae medidas: escala sin verificar'
    if err < 0.10:
        return f, f'{n} (coincide con la ficha: {largo_ficha_cm} cm)', None

    f, n = (0.001, 'mm') if mayor > 20 else ((0.01, 'cm') if mayor > 3 else (1.0, 'm'))
    return f, f'{n} (del archivo, que trae unidades reales)', (
        f'el archivo da {mayor * f * 100:.1f} cm y la ficha dice {largo_ficha_cm} cm '
        f'({err*100:.0f}% de diferencia): se respeta el archivo')


def procesar(archivo, catalogo, revisar=False):
    nombre = os.path.basename(archivo)
    m = CODIGO.search(nombre)
    if not m:
        return f'{nombre}: sin código LCDCP-MV en el nombre, se omite'
    numero = m.group(1)
    # el catálogo puede tenerlo con ceros a la izquierda o sin ellos
    pieza = next((p for p in catalogo['piezas']
                  if p['codigo'].split('-')[-1].lstrip('0') == numero.lstrip('0')), None)
    if not pieza:
        return f'{nombre}: la pieza {numero} no está en el catálogo, se omite'
    codigo = pieza['codigo']
    js, bin_ = leer_glb(archivo)
    lo, tam = extension(js)
    if not all(map(lambda v: v == v, tam)):
        return f'{nombre}: sin datos de POSITION'

    d = pieza.get('dimensiones') or {}
    factor, motivo, alerta = unidades(tam, d.get('largo'))

    # ¿la altura quedó en Z? el eje vertical suele ser el de menor recorrido en piezas planas,
    # pero lo que decide es la rotación que trae el nodo: Blender exporta +90° en X
    nodo = js['nodes'][js['scenes'][js.get('scene', 0)]['nodes'][0]]
    rot = nodo.get('rotation')
    z_arriba = bool(rot and abs(rot[0] - 0.7071) < .01 and abs(rot[3] - 0.7071) < .01)

    real = [t * factor for t in tam]
    aviso = (f'{nombre}\n'
             f'    tamaño     {tam[0]:.1f} x {tam[1]:.1f} x {tam[2]:.1f} del archivo\n'
             f'    unidades   {motivo} → {real[0]*1000:.0f} x {real[1]*1000:.0f} x {real[2]*1000:.0f} mm\n'
             f'    eje        {"rotación de Blender: se quita" if z_arriba else "altura en Y, correcto"}'
             + (f'\n    ATENCIÓN   {alerta}' if alerta else ''))
    if revisar:
        return aviso

    if z_arriba:
        nodo.pop('rotation', None)
    nodo['scale'] = [factor] * 3
    nodo['translation'] = [-(lo[k] + tam[k] / 2) * factor for k in range(3)]   # centrado

    tmp = os.path.join(RAIZ, '.ingesta.glb')
    escribir_glb(tmp, js, bin_)

    destino = os.path.join(MODELOS, f'{codigo}.glb')
    movil = os.path.join(MODELOS, 'mobile', f'{codigo}.glb')
    os.makedirs(os.path.dirname(movil), exist_ok=True)
    subprocess.run(CLI + ['optimize', tmp, destino, '--compress', 'draco',
                          '--texture-compress', 'false', '--texture-size', '2048',
                          '--simplify', 'false'], capture_output=True)
    subprocess.run(CLI + ['optimize', tmp, movil, '--compress', 'draco',
                          '--texture-compress', 'webp', '--texture-size', '1024',
                          '--simplify', 'true', '--simplify-ratio', '0.12',
                          '--simplify-error', '0.003'], capture_output=True)
    os.remove(tmp)

    pieza['media']['modelo'] = f'assets/models/{codigo}.glb'
    pieza['media']['modelo_movil'] = f'assets/models/mobile/{codigo}.glb'
    pieza.setdefault('camara', {'phi': 30, 'giro': 60, 'rango': 40, 'libre': True})
    pieza.setdefault('visor_relieve', f'visor.html?id={codigo}')

    return (aviso + f'\n    publicado  {os.path.getsize(destino)/1e6:.1f} MB · '
                    f'móvil {os.path.getsize(movil)/1024:.0f} KB')


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    revisar = '--revisar' in sys.argv

    ruta_cat = os.path.join(RAIZ, 'assets', 'data', 'catalogo.json')
    catalogo = json.load(open(ruta_cat, encoding='utf-8'))

    if args:
        archivos = args
    elif os.path.isdir(ENTRADA):
        archivos = sorted(os.path.join(ENTRADA, f)
                          for f in os.listdir(ENTRADA) if f.lower().endswith('.glb'))
    else:
        archivos = []
    if not archivos:
        print(f'no hay .glb que procesar.\n'
              f'  pasa los archivos como argumento, o deja la carpeta de originales en\n'
              f'  {ENTRADA}  (se cambia con la variable MV_ORIGINALES)')
        return

    for a in archivos:
        print(procesar(a, catalogo, revisar), '\n')

    if not revisar:
        # las cifras de la portada salen de aquí: se recalculan, no se escriben a mano
        catalogo['total_piezas'] = len(catalogo['piezas'])
        catalogo['con_modelo_3d'] = sum(
            1 for p in catalogo['piezas'] if (p.get('media') or {}).get('modelo'))
        shutil.copy(ruta_cat, ruta_cat + '.bak')
        json.dump(catalogo, open(ruta_cat, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        # los navegadores cachean por nombre: hay que subir la versión de los medios
        js_cat = os.path.join(RAIZ, 'assets', 'js', 'catalogo.js')
        s = open(js_cat, encoding='utf-8').read()
        v = int(re.search(r'export const V = (\d+);', s).group(1)) + 1
        open(js_cat, 'w', encoding='utf-8').write(
            re.sub(r'export const V = \d+;', f'export const V = {v};', s))
        for pagina in ('pieza.html', 'index.html', 'visor.html'):
            p = os.path.join(RAIZ, pagina)
            t = open(p, encoding='utf-8').read()
            open(p, 'w', encoding='utf-8').write(
                re.sub(r'catalogo\.js\?v=\d+', f'catalogo.js?v={v}', t).replace(
                    f'const V = {v-1};', f'const V = {v};'))
        print(f'catálogo actualizado · versión de medios {v}')


if __name__ == '__main__':
    main()

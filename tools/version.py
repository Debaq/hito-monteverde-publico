#!/usr/bin/env python3
"""Sube la versión de los archivos estáticos para que los navegadores no sirvan lo viejo.

    python tools/version.py            sube uno la versión
    python tools/version.py 12         la fija en 12
    python tools/version.py --ver      sólo informa cuál está puesta

El HTML lleva cabecera de no-cache, así que se revalida en cada visita. Todo lo demás
—css, módulos, catálogo, modelos, imágenes— va con ?v=N, se cachea para siempre y se
renueva sólo cuando este número cambia. Así una actualización no obliga a nadie a
vaciar la caché a mano.
"""
import glob
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS_CATALOGO = os.path.join(RAIZ, 'assets', 'js', 'catalogo.js')

META = ('<meta http-equiv="cache-control" content="no-cache">\n'
        '<meta http-equiv="expires" content="0">')


def paginas():
    return sorted(glob.glob(os.path.join(RAIZ, '*.html')) +
                  glob.glob(os.path.join(RAIZ, 'debug', '*.html')))


def version_actual():
    s = open(JS_CATALOGO, encoding='utf-8').read()
    m = re.search(r'export const V = (\d+);', s)
    return int(m.group(1)) if m else 1


def aplicar(v):
    # el número vive en catalogo.js: de ahí lo toman las páginas para los medios
    s = open(JS_CATALOGO, encoding='utf-8').read()
    open(JS_CATALOGO, 'w', encoding='utf-8').write(
        re.sub(r'export const V = \d+;', f'export const V = {v};', s))

    tocadas = 0
    for p in paginas():
        s = original = open(p, encoding='utf-8').read()

        # todo recurso propio con ?v=N pasa a la versión nueva
        s = re.sub(r'(\.(?:js|css|json|glb|webp|png|pdf))\?v=\d+', rf'\1?v={v}', s)
        # la constante V que algunas páginas usan para armar rutas
        s = re.sub(r'const V = \d+;', f'const V = {v};', s)
        # css sin versionar todavía
        s = re.sub(r'(href="(?:\.\./)?assets/css/app\.css)"', rf'\1?v={v}"', s)

        if 'http-equiv="cache-control"' not in s:
            s = s.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + META, 1)

        if s != original:
            open(p, 'w', encoding='utf-8').write(s)
            tocadas += 1
    return tocadas


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if '--ver' in sys.argv:
        print(f'versión actual: {version_actual()}')
        return
    v = int(arg[0]) if arg else version_actual() + 1
    n = aplicar(v)
    print(f'versión {v} · {n} páginas actualizadas')
    print('el HTML se revalida solo; el resto se cachea hasta el próximo cambio de versión')


if __name__ == '__main__':
    main()

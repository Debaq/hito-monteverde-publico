#!/usr/bin/env python3
"""Arma sitemap.xml desde el catálogo, para que los buscadores encuentren cada ficha.

    python tools/sitemap.py

Las fichas se generan en el navegador desde catalogo.json, así que un buscador que
entra por el índice no siempre llega a las quince. El sitemap se las da de una vez.
Correrlo cada vez que entra o sale una pieza del catálogo.
"""
import json
import os
from xml.sax.saxutils import escape

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = 'https://tecmedhub.org/hitomonteverde/'

# Las páginas con contenido propio. ar.html y visor.html son herramientas que se
# abren desde la ficha o el cartel; huella.html sólo redirige.
PAGINAS = ['', 'catalogo.html', 'panorama.html', 'libro.html']


def main():
    with open(os.path.join(RAIZ, 'assets', 'data', 'catalogo.json'), encoding='utf-8') as f:
        piezas = json.load(f)['piezas']

    urls = [SITIO + p for p in PAGINAS]
    urls += [f"{SITIO}pieza.html?id={p['codigo']}" for p in piezas]

    lineas = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lineas += [f'  <url><loc>{escape(u)}</loc></url>' for u in urls]
    lineas.append('</urlset>')

    destino = os.path.join(RAIZ, 'sitemap.xml')
    with open(destino, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lineas) + '\n')
    print(f'sitemap.xml: {len(urls)} direcciones')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Genera los impresos de la ruta: los carteles de pieza y las hojas de QR.

    python tools/impresos.py placas          las piezas con modelo 3D
    python tools/impresos.py placas LCDCP-MV-00008
    python tools/impresos.py carta todas     incluye tambien las que no tienen modelo
    python tools/impresos.py qr              sólo los carteles de QR (no toca los de pieza)

Salida en assets/impresos/. El mapa de IDs queda en assets/data/marcadores.json,
que es lo que lee el sitio para saber qué marcador corresponde a qué pieza.
"""
import json
import os
import sys
from functools import lru_cache
from functools import lru_cache

import cv2
import cv2.aruco as aruco
import numpy as np
from reportlab.lib.colors import Color, black, white
from reportlab.lib.pagesizes import A4, A5, letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, 'assets', 'impresos')
DICC = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)

# medidas de impresión
CARTEL = (140 * mm, 214 * mm)  # tamaño final del cartel, vertical
SANGRADO = 5 * mm              # margen de papel alrededor, para poder cortar
LADO_PLACA = 52 * mm           # marcador en el cartel: lee cómodo hasta ~36 cm
LADO_SALTO = 45 * mm           # el marcador del cartel de QR: se lee de pie, a un metro
ALTO_LOGO = 12.5 * mm          # tope del alto común de los logos del pie
SEPARA_LOGO = 6 * mm           # aire entre un logo y el otro
LOGOS_PIE = ('logo arqueo.jpeg', 'logo tecmed.jpeg')
UACH_VECES = 1.5               # el de la cabecera, vez y media los del pie

# se imprime en A4; la carta queda al lado por si toca una impresora gringa
HOJAS = {'A4': A4, 'carta': letter}

SITIO = 'https://tecmedhub.org/hitomonteverde/'
# las hojas de QR: la de entrada lleva la experiencia grande y las dos puertas chicas
HOJAS_QR = [
    {'titulo': 'Realidad aumentada',
     'bajada': 'Apunta la cámara a los códigos de la ruta y la pieza aparece sobre el papel',
     'grande': ('Entrar a la experiencia', SITIO + 'ar.html'),
     'chicos': [('El sitio', SITIO), ('Catálogo', SITIO + 'catalogo.html')]},
    {'titulo': 'Sitio 360°',
     'bajada': 'Así se ve hoy Monte Verde. Mira alrededor moviendo el teléfono',
     'grande': ('Mirar el sitio en 360°', SITIO + 'panorama.html'),
     'chicos': [],
     'foto': True,
     # este cartel va en mitad del paseo, cuando el visitante ya trae la cámara abierta:
     # se apunta igual que los de pieza. Sin QR, porque un QR no lo lee el visor en todos
     # los teléfonos y aquí no hay nadie que llegue de cero.
     'salto': 'panorama'},
    {'titulo': 'Libro de visitas',
     'bajada': 'Deja lo que te llevas de Monte Verde y lee lo que escribieron otros',
     'grande': ('Firmar el libro', SITIO + 'libro.html'),
     'chicos': []},
]

OCRE = Color(0.816, 0.514, 0.012)
GRIS = Color(0.42, 0.40, 0.37)

def imagen_marcador(marker_id, px=1200):
    """ArUco como ImageReader, con zona de silencio blanca de 1 módulo."""
    img = aruco.generateImageMarker(DICC, marker_id, px, borderBits=1)
    rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    from PIL import Image
    return ImageReader(Image.fromarray(rgb))


def bits_marcador(marker_id):
    """Los 16 módulos de datos del marcador, sin el borde negro."""
    img = DICC.generateImageMarker(marker_id, 6, borderBits=1)
    return (img[1:5, 1:5] > 0).astype(int)


def distancia_marcadores(a, b):
    """Módulos en que se diferencian dos ids, en la rotación más parecida.

    En un 4x4 hay 16 módulos y lo normal en este diccionario es que dos ids difieran en
    4. Cuanto más alto, más tiene que fallar la lectura para devolver el id equivocado.
    """
    A, B = bits_marcador(a), bits_marcador(b)
    return min(int(np.sum(A != np.rot90(B, k))) for k in range(4))


def elegir_id(usados, total=100):
    """El id libre que más se diferencia de los que ya están en uso."""
    libres = [i for i in range(total) if i not in usados]
    return max(libres, key=lambda i: (min(distancia_marcadores(i, u) for u in usados), i))


def cargar_catalogo():
    with open(os.path.join(RAIZ, 'assets', 'data', 'catalogo.json'), encoding='utf-8') as f:
        return json.load(f)['piezas']


def con_modelo(p):
    """Si la pieza tiene modelo 3D.

    El cartel es la puerta a la realidad aumentada: sin modelo, quien apunta la camara
    solo consigue la misma fotografia que ya esta en la ficha. Esas cinco piezas se
    dejan fuera salvo que se pidan con `todas`.
    """
    return bool(p['media'].get('modelo') or p['media'].get('modelo_movil'))


def asignar_ids(piezas):
    """Un id por pieza, 0..14, en el orden del catálogo.

    Los cubos de mano ocupaban seis ids cada uno —uno por cara— y se llevaban 60 de
    los 100 del diccionario. Nunca se armaron, así que se quitaron: con ellos fuera,
    esos ids dejan de estar asociados a ninguna pieza y una lectura dudosa ya no puede
    devolver una pieza que no es.
    """
    mapa = {'diccionario': 'DICT_4X4_100', 'placa_mm': LADO_PLACA / mm, 'placas': {}}
    for i, p in enumerate(piezas):
        mapa['placas'][p['codigo']] = i
    return mapa


def texto(c, x, y, txt, fuente='Helvetica', tam=10, color=black, espaciado=0):
    c.setFillColor(color)
    c.setFont(fuente, tam)
    if espaciado:                      # reportlab no expone setCharSpace: se dibuja letra a letra
        for ch in txt:
            c.drawString(x, y, ch)
            x += c.stringWidth(ch, fuente, tam) + espaciado
    else:
        c.drawString(x, y, txt)


def imagen_pieza(codigo):
    """La foto recortada si existe (fondo transparente), si no la completa."""
    for ruta in (os.path.join(RAIZ, 'assets', 'images', 'recortes', f'{codigo}.webp'),
                 os.path.join(RAIZ, 'assets', 'images', 'mobile', f'{codigo}.webp')):
        if os.path.exists(ruta):
            from PIL import Image
            return Image.open(ruta).convert('RGBA')
    return None


@lru_cache(maxsize=None)
@lru_cache(maxsize=None)
def logo(nombre):
    """Logo de assets/marca listo para el PDF: fondo a blanco puro y sin margen.

    Los JPEG vienen con fondo 247 y aire alrededor: sobre el papel blanco el
    fondo se ve como un recuadro y el aire hace que un logo se vea más chico
    que otro aunque se dibujen al mismo alto. Se blanquea y se recorta.
    No se toca el color: los archivos ya vienen como se quieren impresos.
    """
    from PIL import Image
    ruta = os.path.join(RAIZ, 'assets', 'marca', nombre)
    if not os.path.exists(ruta):
        return None
    im = Image.open(ruta).convert('RGB')
    a = np.array(im)
    blanco = (a >= 238).all(axis=2)
    a[blanco] = 255
    filas, cols = np.where(~blanco)
    if len(filas):
        a = a[filas.min():filas.max() + 1, cols.min():cols.max() + 1]
    return Image.fromarray(a)


def alto_logos(ancho_disp):
    """El alto común más grande con el que los logos del pie caben en ese ancho."""
    ims = [im for im in (logo(n) for n in LOGOS_PIE) if im is not None]
    if not ims:
        return ALTO_LOGO
    veces = sum(im.width / im.height for im in ims)       # ancho total si el alto fuera 1
    return min(ALTO_LOGO, (ancho_disp - SEPARA_LOGO * (len(ims) - 1)) / veces)


def poner_logo(c, im, x, y, alto=ALTO_LOGO, derecha=False):
    """Dibuja el logo con ese alto; devuelve el ancho que ocupó."""
    if im is None:
        return 0
    ancho = alto * im.width / im.height
    c.drawImage(ImageReader(im), x - ancho if derecha else x, y, ancho, alto)
    return ancho


def texto_medidas(pieza):
    """'Medida: 4,1 x 1,2 x 0,7 cm' — coma decimal, como se escribe acá."""
    d = pieza.get('dimensiones') or {}
    partes = [f'{d[k]:g}'.replace('.', ',') for k in ('largo', 'ancho', 'espesor')
              if d.get(k) is not None]
    if not partes:
        return ''
    return f"Medida: {' x '.join(partes)} {d.get('unidad', 'cm')}"


def en_lineas(c, txt, ancho, fuente='Helvetica', tam=9.5):
    """Parte el texto en líneas que quepan en ese ancho."""
    lineas = ['']
    for palabra in txt.split():
        prueba = f'{lineas[-1]} {palabra}'.strip()
        if lineas[-1] and c.stringWidth(prueba, fuente, tam) > ancho:
            lineas.append(palabra)
        else:
            lineas[-1] = prueba
    return lineas


def titulo_en_lineas(c, txt, libre, tam=17):
    """El nombre de la pieza en el cuerpo más grande que quepa junto al logo.

    Primero achica hasta 14 pt; si aún no entra, lo parte en dos líneas.
    """
    while tam > 14 and c.stringWidth(txt, 'Helvetica-Bold', tam) > libre:
        tam -= .5
    if c.stringWidth(txt, 'Helvetica-Bold', tam) <= libre:
        return tam, [txt]

    palabras, lineas = txt.split(), ['']
    for p in palabras:
        prueba = f'{lineas[-1]} {p}'.strip()
        if lineas[-1] and c.stringWidth(prueba, 'Helvetica-Bold', tam) > libre:
            lineas.append(p)
        else:
            lineas[-1] = prueba
    while tam > 10 and max(c.stringWidth(l, 'Helvetica-Bold', tam) for l in lineas) > libre:
        tam -= .5                              # una palabra sola más ancha que el hueco
    return tam, lineas


def marco_corte(c, ox, oy):
    """Recuadro del cartel y marcas en las esquinas, para tijera o guillotina."""
    ancho_c, alto_c = CARTEL
    c.setStrokeColor(black)
    c.setLineWidth(.6)
    c.rect(ox, oy, ancho_c, alto_c, stroke=1, fill=0)
    largo = 4 * mm
    for x in (ox, ox + ancho_c):
        for y in (oy, oy + alto_c):
            c.line(x, y - SANGRADO, x, y - SANGRADO + largo) if y == oy else None
            c.line(x, y + SANGRADO, x, y + SANGRADO - largo) if y != oy else None
            c.line(x - SANGRADO, y, x - SANGRADO + largo, y) if x == ox else None
            c.line(x + SANGRADO, y, x + SANGRADO - largo, y) if x != ox else None
    texto(c, ox, oy - 3.2 * mm, f'cortar por el recuadro · {ancho_c/mm:.0f} x {alto_c/mm:.0f} mm',
          'Helvetica', 5.5, Color(.55, .55, .55))


def flecha_abajo(c, x, y, lado):
    """Flecha gruesa apuntando al suelo, del tamaño que ocupaba el marcador.

    Va en el cartel de las piezas cuyo código está pegado en el piso: ahí no sirve
    imprimir el marcador otra vez —se leería el del papel y no el del vinilo, que es
    el que tiene el tamaño con el que se calcula la distancia—.
    """
    ancho_palo = lado * .34
    alto_punta = lado * .42
    cx = x + lado / 2
    c.setFillColor(OCRE)
    c.setStrokeColor(OCRE)
    p = c.beginPath()
    p.moveTo(cx - ancho_palo / 2, y + lado)                    # arranca arriba a la izquierda
    p.lineTo(cx + ancho_palo / 2, y + lado)
    p.lineTo(cx + ancho_palo / 2, y + alto_punta)
    p.lineTo(cx + lado / 2, y + alto_punta)                    # ala derecha de la punta
    p.lineTo(cx, y)                                            # vértice, abajo
    p.lineTo(cx - lado / 2, y + alto_punta)                    # ala izquierda
    p.lineTo(cx - ancho_palo / 2, y + alto_punta)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def dibujar_placa(c, pieza, marker_id, ox, oy, en_suelo=False):
    """Dibuja el cartel de 140 x 214 mm con su esquina inferior izquierda en (ox, oy)."""
    ancho_c, alto_c = CARTEL
    margen = 12 * mm

    # --- encabezado: codigo, titulo y bajada a la izquierda; el logo UACh a la derecha
    x_txt = ox + margen + LADO_PLACA + 7 * mm            # donde empieza la banda de abajo
    alto_pie = alto_logos(ox + ancho_c - margen - x_txt)
    alto_uach = alto_pie * UACH_VECES
    ancho_uach = poner_logo(c, logo('logo uach.jpeg'), ox + ancho_c - margen,
                            oy + alto_c - 13 * mm - alto_uach, alto_uach, derecha=True)
    libre = ancho_c - 2 * margen - (ancho_uach + 8 * mm if ancho_uach else 0)

    texto(c, ox + margen, oy + alto_c - 18 * mm, pieza['codigo'], 'Helvetica-Bold', 8, GRIS, 1.1)
    tam, lineas = titulo_en_lineas(c, pieza['denominacion'], libre)
    y = oy + alto_c - 27 * mm
    for linea in lineas:
        texto(c, ox + margen, y, linea, 'Helvetica-Bold', tam)
        y -= tam * 1.15
    y += tam * 1.15                            # la base de la última línea del título

    y_bajada = y - 7 * mm
    if pieza.get('tipo_objeto'):
        texto(c, ox + margen, y_bajada, pieza['tipo_objeto'], 'Helvetica', 9.5, GRIS)
    y_linea = min(y_bajada - 5 * mm, oy + alto_c - 13 * mm - alto_uach - 3 * mm)
    c.setStrokeColor(OCRE)
    c.setLineWidth(1.8)
    c.line(ox + margen, y_linea, ox + ancho_c - margen, y_linea)

    # --- la pieza, centrada y lo más grande que permita el espacio libre
    caja_y0 = oy + 76 * mm
    caja_y1 = y_linea - 7 * mm
    caja_x0, caja_x1 = ox + margen, ox + ancho_c - margen
    im = imagen_pieza(pieza['codigo'])
    if im is not None:
        esc = min((caja_x1 - caja_x0) / im.width, (caja_y1 - caja_y0) / im.height)
        w, h = im.width * esc, im.height * esc
        c.drawImage(ImageReader(im), ox + (ancho_c - w) / 2, caja_y0 + (caja_y1 - caja_y0 - h) / 2,
                    w, h, mask='auto')

    # --- banda inferior: marcador, medidas y espacio reservado para los logos
    y_banda = oy + 14 * mm
    if en_suelo:
        flecha_abajo(c, ox + margen, y_banda, LADO_PLACA)
        texto(c, x_txt, y_banda + LADO_PLACA - 6 * mm, 'El código está', 'Helvetica-Bold', 9.5, OCRE)
        texto(c, x_txt, y_banda + LADO_PLACA - 11.5 * mm, 'en el suelo', 'Helvetica-Bold', 9.5, OCRE)
    else:
        c.drawImage(imagen_marcador(marker_id), ox + margen, y_banda, LADO_PLACA, LADO_PLACA)
        texto(c, ox + margen, y_banda - 4.5 * mm, f'id {marker_id}', 'Helvetica', 6.5, GRIS)
        texto(c, x_txt, y_banda + LADO_PLACA - 6 * mm, 'Apunta este código', 'Helvetica-Bold', 9.5, OCRE)
        texto(c, x_txt, y_banda + LADO_PLACA - 11.5 * mm, 'con la cámara', 'Helvetica-Bold', 9.5, OCRE)

    medidas = texto_medidas(pieza)
    if medidas:
        texto(c, x_txt, y_banda + LADO_PLACA - 19 * mm, medidas, 'Helvetica', 9, GRIS)
    if pieza.get('sitio'):
        texto(c, x_txt, y_banda + LADO_PLACA - 25 * mm, pieza['sitio'], 'Helvetica', 8.5, GRIS)

    # logos institucionales, al mismo alto que el de la cabecera
    x_logo = x_txt
    for nombre in LOGOS_PIE:
        ancho_l = poner_logo(c, logo(nombre), x_logo, y_banda, alto_pie)
        if ancho_l:
            x_logo += ancho_l + SEPARA_LOGO

    marco_corte(c, ox, oy)


def foto_sitio():
    """La aérea del sitio que abre el catálogo impreso, para el cartel del 360.

    Sale de la portada del PDF (`assets/images/sitio-monte-verde.webp`, recortada de ahí).
    Las del visor no servían en papel: la equirectangular sintética sale con el cielo
    estirado, y la real tiene los bordes difuminados y se ve sucia sobre blanco.
    """
    ruta = os.path.join(RAIZ, 'assets', 'images', 'sitio-monte-verde.webp')
    if not os.path.exists(ruta):
        return None
    from PIL import Image
    return Image.open(ruta).convert('RGB')


def qr(c, url, x, y, lado, nivel='M'):
    """Un QR de `lado` puntos con su esquina inferior izquierda en (x, y).

    Lo dibuja reportlab, que ya trae el codificador: nada que instalar aparte.
    """
    w = QrCodeWidget(url, barLevel=nivel, barBorder=4)
    b = w.getBounds()
    d = Drawing(lado, lado, transform=[lado / (b[2] - b[0]), 0, 0, lado / (b[3] - b[1]), 0, 0])
    d.add(w)
    renderPDF.draw(d, c, x, y)


ALTO_ETIQUETA = 8 * mm             # lo que baja la etiqueta bajo un QR


def centrado(c, txt, cx, y, fuente, tam, color):
    """Texto centrado en cx; devuelve su ancho."""
    ancho = c.stringWidth(txt, fuente, tam)
    texto(c, cx - ancho / 2, y, txt, fuente, tam, color)
    return ancho


def bloque_qr(c, url, etiqueta, cx, y, lado, tam=17):
    """QR centrado en `cx` con su nombre debajo.

    Sin la dirección impresa: repetirla bajo cada QR se comía el espacio y en un cartel
    con tres códigos nadie la va a copiar tres veces. Va una sola, en el pie.
    Los cuerpos van gruesos a propósito: esto se lee de pie y a un metro.
    """
    qr(c, url, cx - lado / 2, y, lado)
    centrado(c, etiqueta, cx, y - (tam * .55 + 3 * mm), 'Helvetica-Bold', tam, OCRE)


def dibujar_cartel_qr(c, titulo, bajada, grande, chicos, ox, oy, foto=False, salto_id=None):
    """Cartel de QR del mismo tamaño que los de pieza: se recorta y va al mismo soporte.

    Es la puerta de entrada al sitio, sin marcador de por medio: el QR grande manda y
    los chicos son los atajos de al lado.
    """
    ancho_c, alto_c = CARTEL
    margen = 12 * mm
    x0, x1 = ox + margen, ox + ancho_c - margen
    alto = oy + alto_c                          # el borde de arriba del cartel

    # --- cabecera, igual que la de los carteles: logo UACh a la derecha y línea ocre
    alto_pie = alto_logos(x1 - x0)
    alto_uach = alto_pie * UACH_VECES
    ancho_uach = poner_logo(c, logo('logo uach.jpeg'), x1, alto - 13 * mm - alto_uach,
                            alto_uach, derecha=True)
    libre = (x1 - x0) - (ancho_uach + 8 * mm if ancho_uach else 0)

    tam, lineas = titulo_en_lineas(c, titulo, libre, tam=22)
    y = alto - 21 * mm
    for linea in lineas:
        texto(c, x0, y, linea, 'Helvetica-Bold', tam)
        y -= tam * 1.15
    y += tam * 1.15
    # la bajada se envuelve dentro del hueco que deja el logo: antes se le metía debajo
    y -= 8 * mm
    for linea in en_lineas(c, bajada, libre, tam=12):
        texto(c, x0, y, linea, 'Helvetica', 12, GRIS)
        y -= 5.6 * mm
    y_linea = min(y - 1 * mm, alto - 13 * mm - alto_uach - 3 * mm)
    c.setStrokeColor(OCRE)
    c.setLineWidth(1.8)
    c.line(x0, y_linea, x1, y_linea)

    # --- pie: los logos abajo a la izquierda, la dirección del sitio a la derecha
    y_pie = oy + 14 * mm
    x_logo = x0
    for nombre in LOGOS_PIE:
        ancho_l = poner_logo(c, logo(nombre), x_logo, y_pie, alto_pie)
        if ancho_l:
            x_logo += ancho_l + SEPARA_LOGO
    # la dirección escrita sólo va donde hay QR: es la vía para quien llega de cero.
    # En el cartel de marcador no pinta nada y le robaba alto a la fotografía.
    cx = (x0 + x1) / 2
    techo_chicos = y_pie + alto_pie + 10 * mm
    if salto_id is None:
        const_y = y_pie + alto_pie + 12 * mm
        centrado(c, SITIO.replace('https://', '').rstrip('/'), cx, const_y,
                 'Helvetica-Bold', 13, GRIS)
        centrado(c, 'o escríbelo en el navegador', cx, const_y - 5 * mm, 'Helvetica', 9, GRIS)
        techo_chicos = const_y + 11 * mm
    if chicos:
        lado_chico = 36 * mm
        y_chico = techo_chicos + ALTO_ETIQUETA
        paso = (x1 - x0) / len(chicos)
        for i, (etiqueta, url) in enumerate(chicos):
            bloque_qr(c, url, etiqueta, x0 + paso * (i + .5), y_chico, lado_chico, 14)
        techo_chicos = y_chico + lado_chico + 8 * mm

    # --- la foto del sitio, pegada bajo la línea: dice de qué va esto antes de leer nada
    techo = y_linea - 10 * mm
    if foto:
        im = foto_sitio()
        if im is not None:
            ancho_f = x1 - x0
            alto_f = min(ancho_f * im.height / im.width, 54 * mm if salto_id is None else 90 * mm)
            techo = y_linea - 8 * mm - alto_f
            c.drawImage(ImageReader(im), x0, techo, ancho_f, alto_f)
            techo -= 4 * mm

    # --- el grande, centrado en lo que queda entre lo de arriba y lo de abajo
    etiqueta, url = grande
    hueco_alto = techo - techo_chicos
    if salto_id is None:
        lado = min(x1 - x0, hueco_alto - ALTO_ETIQUETA)
        y_grande = techo_chicos + (hueco_alto - lado - ALTO_ETIQUETA) / 2 + ALTO_ETIQUETA
        bloque_qr(c, url, etiqueta, cx, y_grande, lado)
    else:
        # dos puertas a lo mismo: el QR para quien llega con la cámara del teléfono y el
        # marcador para quien ya está en el visor, que no sabe leer códigos QR
        # el marcador solo: el título de arriba ya dice qué es esto
        lado = min(x1 - x0, hueco_alto, LADO_PLACA)
        y_grande = techo_chicos + (hueco_alto - lado) / 2
        c.drawImage(imagen_marcador(salto_id), cx - lado / 2, y_grande, lado, lado)

    marco_corte(c, ox, oy)


def carteles_qr_en_hoja(ruta, saltos, hoja=A4):
    """Los carteles de QR, uno por página y centrados como los de pieza."""
    ancho, alto = hoja
    c = canvas.Canvas(ruta, pagesize=hoja)
    for h in HOJAS_QR:
        c.setFillColor(white)
        c.rect(0, 0, ancho, alto, stroke=0, fill=1)
        dibujar_cartel_qr(c, h['titulo'], h['bajada'], h['grande'], h['chicos'],
                          (ancho - CARTEL[0]) / 2, (alto - CARTEL[1]) / 2, h.get('foto'),
                          saltos.get(h.get('salto', ''), {}).get('id'))
        c.showPage()
    c.save()
    return len(HOJAS_QR)


def placa(pieza, marker_id, ruta, en_suelo=False):
    """Un cartel por archivo, en hoja del tamaño justo más el sangrado."""
    ancho, alto = CARTEL[0] + 2 * SANGRADO, CARTEL[1] + 2 * SANGRADO
    c = canvas.Canvas(ruta, pagesize=(ancho, alto))
    c.setFillColor(white)
    c.rect(0, 0, ancho, alto, stroke=0, fill=1)
    dibujar_placa(c, pieza, marker_id, SANGRADO, SANGRADO, en_suelo)
    c.showPage()
    c.save()


def carteles_en_hoja(piezas, mapa, ruta, hoja=A4):
    """Los carteles en un PDF, uno por página y centrados en la hoja.

    Es para imprimir de una sola vez: la impresora común no sabe de hojas de 150 x 224.
    """
    ancho, alto = hoja
    c = canvas.Canvas(ruta, pagesize=hoja)
    for p in piezas:
        c.setFillColor(white)
        c.rect(0, 0, ancho, alto, stroke=0, fill=1)
        dibujar_placa(c, p, mapa['placas'][p['codigo']],
                      (ancho - CARTEL[0]) / 2, (alto - CARTEL[1]) / 2,
                      p['codigo'] in mapa.get('suelo', {}))
        c.showPage()
    c.save()
    return len(piezas)


def main():
    modo = sys.argv[1] if len(sys.argv) > 1 else 'carta'
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    todas = arg == 'todas'
    filtro = None if todas else arg

    completo = cargar_catalogo()
    mapa = asignar_ids(completo)          # los ids salen del catálogo entero: no se mueven
    piezas = completo if todas else [p for p in completo if con_modelo(p)]
    fuera = [p for p in completo if p not in piezas]
    os.makedirs(SALIDA, exist_ok=True)
    ruta_mapa = os.path.join(RAIZ, 'assets', 'data', 'marcadores.json')
    if os.path.exists(ruta_mapa):                 # los marcadores de suelo los pone vinilo.py
        with open(ruta_mapa, encoding='utf-8') as f:
            anterior = json.load(f)
        if anterior.get('suelo'):
            mapa['suelo'] = anterior['suelo']
        if anterior.get('saltos'):
            mapa['saltos'] = anterior['saltos']

    # los marcadores que no son piezas sino atajos a otra página del sitio
    mapa.setdefault('saltos', {})
    for h in HOJAS_QR:
        clave = h.get('salto')
        if not clave or clave in mapa['saltos']:
            continue
        usados = set(mapa['placas'].values()) | {v['id'] for v in mapa.get('suelo', {}).values()}
        usados |= {v['id'] for v in mapa['saltos'].values()}
        mapa['saltos'][clave] = {'id': elegir_id(usados), 'lado_mm': LADO_SALTO / mm,
                                 'destino': h['grande'][1].replace(SITIO, '')}
    with open(ruta_mapa, 'w', encoding='utf-8') as f:
        json.dump(mapa, f, ensure_ascii=False, indent=2)

    if modo == 'qr':
        # sólo los carteles de QR: los de pieza pesan 26 MB cada uno y van por Git LFS, así
        # que rehacerlos sin cambios sube 52 MB nuevos al repositorio por nada
        for nombre, hoja in HOJAS.items():
            rq = os.path.join(SALIDA, f'TODOS-QR-{nombre}.pdf')
            n3 = carteles_qr_en_hoja(rq, mapa.get('saltos', {}), hoja)
            print(f'{os.path.relpath(rq, RAIZ)}  ·  {n3} carteles de QR, uno por página')
        for i, h in enumerate(HOJAS_QR, 1):
            print(f'  página {i}: {h["titulo"]}')
        print('imprimir al 100 %, sin "ajustar a página", en papel mate')
        return

    if modo in ('carta', 'hojas', 'A4'):
        # todo junto y en las dos hojas: se abre la que sirva, se imprime y listo
        for nombre, hoja in HOJAS.items():
            rc = os.path.join(SALIDA, f'TODOS-carteles-{nombre}.pdf')
            rq = os.path.join(SALIDA, f'TODOS-QR-{nombre}.pdf')
            n1 = carteles_en_hoja(piezas, mapa, rc, hoja)
            n3 = carteles_qr_en_hoja(rq, mapa.get('saltos', {}), hoja)
            print(f'{os.path.relpath(rc, RAIZ)}  ·  {n1} carteles, uno por página')
            print(f'{os.path.relpath(rq, RAIZ)}  ·  {n3} carteles de QR, uno por página')
        if fuera:
            print(f'sin modelo 3D, fuera del PDF ({len(fuera)}): '
                  + ', '.join(p['codigo'] for p in fuera))
            print('para incluirlas: python tools/impresos.py carta todas')
        print('imprimir al 100 %, sin "ajustar a página", en papel mate')
        return

    # pedir una pieza por su código la imprime aunque no tenga modelo: si alguien la
    # nombra, la quiere
    hechos = []
    for p in (completo if filtro else piezas):
        if filtro and p['codigo'] != filtro:
            continue
        if modo == 'placas':
            ruta = os.path.join(SALIDA, f"placa-{p['codigo']}.pdf")
            placa(p, mapa['placas'][p['codigo']], ruta, p['codigo'] in mapa.get('suelo', {}))
            hechos.append(ruta)

    for h in hechos:
        print(os.path.relpath(h, RAIZ))
    print(f'{len(hechos)} archivo(s)')


def indice():
    """Pagina de descarga de los impresos.

    index.html enlaza a assets/impresos/. Sin esto, la carpeta depende de que el
    servidor tenga listado de directorios activado, que en la mayoria de los hostings
    estaticos esta apagado y devuelve 403.
    """
    filas = []
    for nombre in sorted(os.listdir(SALIDA)):
        ruta = os.path.join(SALIDA, nombre)
        if nombre == 'index.html' or not os.path.isfile(ruta):
            continue
        kb = os.path.getsize(ruta) / 1024
        peso = f'{kb/1024:.1f} MB' if kb > 1024 else f'{kb:.0f} KB'
        filas.append(f'<li><a href="{nombre}">{nombre}</a> <span>{peso}</span></li>')

    pngs = os.path.join(SALIDA, 'png')
    sueltos = ''
    if os.path.isdir(pngs):
        items = sorted(f for f in os.listdir(pngs) if f.endswith('.png'))
        sueltos = ('<h2>Marcadores sueltos</h2>\n<p class="muted">Para pegar sobre otro '
                   'soporte. Necesitan borde blanco propio de al menos 3,5 cm o no '
                   'detectan.</p>\n<ul class="rejilla">'
                   + ''.join(f'<li><a href="png/{f}">{f[:-4]}</a></li>' for f in items)
                   + '</ul>')

    html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Impresos — Monte Verde</title>
<meta name="robots" content="noindex">
<link rel="icon" href="../marca/icono.svg" type="image/svg+xml">
<link rel="stylesheet" href="../css/app.css">
<style>
  ul {{ list-style: none; padding: 0; display: grid; gap: 8px; max-width: 620px; }}
  li {{ display: flex; gap: 12px; align-items: baseline; padding: 11px 14px;
       background: var(--soil-mid); border: 1px solid var(--line); border-radius: var(--radius); }}
  li span {{ margin-left: auto; font-size: 12.5px; color: var(--sand-500); }}
  .rejilla {{ grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); max-width: none; }}
  .rejilla li {{ font-size: 12.5px; }}
</style>
</head>
<body>
<header class="topbar"><a class="mark" href="../../index.html">Monte <em>Verde</em></a></header>
<main class="wrap">
  <div class="section-title"><h1>Impresos de la ruta</h1></div>
  <p class="muted">Imprimir al 100 %, sin «ajustar a pagina», en papel mate.
     Los carteles van a 140 × 214 mm.</p>
  <ul>{''.join(filas)}</ul>
  {sueltos}
  <p style="margin-top:26px"><a class="btn" href="../../index.html">Volver al inicio</a></p>
</main>
</body>
</html>
"""
    destino = os.path.join(SALIDA, 'index.html')
    open(destino, 'w', encoding='utf-8').write(html)
    return destino


if __name__ == '__main__':
    main()
    print(os.path.relpath(indice(), RAIZ))

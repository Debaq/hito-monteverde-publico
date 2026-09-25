# Hito Monte Verde — ruta interactiva

Sitio móvil de apoyo a un recorrido físico del programa **Restitución e Instalación del
Patrimonio Arqueológico Monte Verde** (GORE Los Lagos / SERPAT / UACh Puerto Montt).

El sitio no es el objeto principal: articula la visita. En cada estación hay un marcador
en la pared; el visitante lo apunta con el teléfono, ve la pieza (3D o 2D), descarga el
catálogo y responde una encuesta.

**Sitio en funcionamiento: <https://tecmedhub.org/hitomonteverde/>**

---

## Por qué faltan los assets

Este repositorio es la versión pública del código, publicada en Zenodo para tener un
DOI citable. **Contiene el código y la documentación, pero no el material del sitio**:

| carpeta quitada | qué tenía |
|---|---|
| `assets/images/` | fotografías de las 15 piezas (original y móvil) |
| `assets/models/` | modelos 3D `.glb` con Draco (escritorio y móvil) |
| `assets/pano/` | panorámica 360 del sitio y parche de foto real |
| `assets/catalogo/` | páginas del catálogo, miniaturas y PDF de descarga |
| `assets/impresos/` | carteles, placas con marcadores ArUco, QR y vinilos de corte |
| `assets/marca/` | logotipos, íconos, tarjeta para compartir y fotos del equipo |
| `assets/fonts/` | Fraunces y Plus Jakarta Sans en woff2 |
| `assets/data/huella-altura.png` | mapa de altura de la huella, derivado del escaneo |
| `assets/data/huella-contorno.json` | mediciones de trabajo sobre la huella, no publicadas |

Las fotografías, los modelos 3D y el catálogo son registros de piezas de la colección
arqueológica de Monte Verde y no nos corresponde redistribuirlos: sus derechos son del
programa y de sus titulares. Los logotipos son de cada institución. Además pesan
cerca de 180 MB, la mayoría modelos 3D.

Por eso **el sistema no funciona completo a partir de este repositorio**: las páginas
cargan, pero las fotos, los modelos, la panorámica y el catálogo no aparecen, y la
cámara AR no tiene qué mostrar. Para ver el sistema andando, con todo su material, hay
que ir a **<https://tecmedhub.org/hitomonteverde/>**.

Lo que sí está completo:

- todas las páginas (`*.html`), estilos (`assets/css/`) y módulos (`assets/js/`);
- los datos estructurados (`assets/data/*.json`): catálogo de piezas, marcadores,
  recortes y páginas del catálogo, que dicen qué archivo espera cada página y dónde;
- las bibliotecas de terceros en `assets/vendor/` (three.js, model-viewer, Draco,
  js-aruco2), con su propia licencia;
- la analítica en PHP (`analitica/`), sin la configuración ni los datos de visitas;
- las herramientas de preparación (`tools/`): cómo se derivó cada imagen, modelo,
  impreso y marcador a partir de los originales.

Quien quiera levantarlo con material propio puede seguir `assets/data/catalogo.json`:
cada pieza trae las rutas a su foto y su modelo, y las secciones de más abajo explican
cómo se generó cada archivo.

---

## Autores

- Nicolás Baier-Quezada — [0000-0003-2818-0990](https://orcid.org/0000-0003-2818-0990)
- Vanessa Uribe-Hernandez — [0009-0003-0795-7921](https://orcid.org/0009-0003-0795-7921)
- Fernanda Lopez-Moncada — [0000-0002-0810-7684](https://orcid.org/0000-0002-0810-7684)
- Haydee Barrientos-Toledo — [0000-0002-3306-4161](https://orcid.org/0000-0002-3306-4161)
- Ricardo Alvarez-Abel — [0000-0003-2089-2037](https://orcid.org/0000-0003-2089-2037)
- Marco Alvarez — [0000-0002-6652-6465](https://orcid.org/0000-0002-6652-6465)

TecMedHub, Universidad Austral de Chile (Sede Puerto Montt).

## Cómo citar

Los metadatos están en [`CITATION.cff`](CITATION.cff) (GitHub ofrece "Cite this
repository") y en [`.zenodo.json`](.zenodo.json).

## Licencia

El código es [MIT](LICENSE). La licencia no alcanza al material que no está en el
repositorio ni a las bibliotecas de `assets/vendor/`: three.js (MIT),
`@google/model-viewer` (Apache-2.0), decodificador Draco (Apache-2.0) y js-aruco2 (MIT).

---

## Sitio

```
index.html      portada: cifras, accesos y grilla de las 15 piezas con filtros
pieza.html      ?id=LCDCP-MV-00008 — destino de los QR/marcadores
panorama.html   360 del sitio con parche real, banderitas y giroscopio
catalogo.html   hojeo por páginas (?p=37), tira de miniaturas y descarga del PDF
visor.html      ?id=… — el 3D con luz rasante, nube de puntos, contorno y molde
ar.html         ?id=… — cámara y marcadores ArUco
encuesta.html   encuesta propia, anónima; las respuestas van a analitica/encuesta.php
libro.html      libro de visitas, sin nombre; lo guarda analitica/libro.php
404.html        enlace viejo o QR mal impreso, dentro del sistema visual
huella.html     redirección de compatibilidad a visor.html?id=LCDCP-MV-02115
```

Sin build: HTML estático y ES modules. **Nada viene de internet**: `three`,
`model-viewer`, el decodificador Draco, `js-aruco2` y las tipografías se sirven desde
`assets/vendor/` y `assets/fonts/`. Es una instalación de museo; si la wifi de la sala
se cae o el firewall institucional bloquea un CDN, el recorrido tiene que seguir
funcionando. Se sube tal cual.

### Sistema visual

Paleta y tipografías alineadas a [tmeduca.org/faunAr](https://tmeduca.org/faunAr/demo/),
en `assets/css/app.css`. Las fuentes son locales (`assets/fonts/`, variables, sólo los
subconjuntos latin y latin-ext):

| token | valor | uso |
|---|---|---|
| `--soil` | `#16110C` | fondo |
| `--soil-mid` | `#211A12` | tarjetas |
| `--line` | `#3A2F20` | bordes |
| `--ochre` | `#D08303` | acento, botón primario |
| `--ochre-light` | `#E9A93C` | acento claro, enlaces |
| `--sage` | `#8C8C7A` | chips secundarios |
| `--crimson` | `#9E1B32` | alertas |
| `--cream` | `#F6F1E8` | títulos y texto fuerte |
| `--sand-300` | `#D9CFBE` | texto base |

Fraunces 600 para títulos, Plus Jakarta Sans para texto. Radios 14 / 22 / pill,
glass `rgba(33,26,18,.62)` con blur 18.

Las escenas 3D dibujan **bajo demanda**: sólo redibujan cuando algo cambia. Una pieza
quieta no consume nada. Es lo que hace que el teléfono no se caliente en una estación
donde la gente deja la pieza abierta un rato.

### Ficha de pieza

Es la página que reciben los QR, así que carga sola sin pasar por la portada. Muestra el
modelo 3D si existe —se carga solo, sin botón de por medio— o la foto con zoom al toque;
datos de la ficha, barra de dimensiones a escala y navegación a la pieza anterior y
siguiente. La chapa sobre el lienzo lleva a `visor.html`, que es donde están la luz
rasante y las capas. Los modelos que sirve son los de `models/mobile/`.

Para sumar una pieza al sitio basta agregarla a `catalogo.json`: no hay HTML por pieza.

## Estructura

```
assets/
  data/       catalogo.json, marcadores.json y los datos de la huella
  images/     *   15 webp a resolución original + mobile/ (1600px)
  models/     *   10 glb con Draco + mobile/ (simplificados)
  pano/       *   360 del sitio (4k y 2k) + parche de foto real
  css/        app.css — tokens y componentes; ar.css y visor.css, lo propio de cada página
  js/         catalogo.js, navegacion.js, sensor.js, analitica.js, offline.js y nube.js
              (la nube de puntos por altura, la misma en el visor y en la cámara AR)
    ar/       la cámara AR por partes: escena, piezas, ajuste, detección, seguimiento,
              gestos, saltos, cámara y calibración (esta sólo con ?debug=1)
    visor/    el visor 3D por partes: vista, luz, materiales, contorno, detalle,
              hoja, lista de piezas, molde y calibración (estos dos, sólo si se usan)
  catalogo/   *   65 páginas webp + thumbs/ + catalogo-monte-verde.pdf (6 MB, el que se descarga)
  impresos/   *   TODOS-carteles, -cubos y -QR, cada uno en A4 y carta, png/ y su index.html
  vendor/     three, model-viewer, decodificador Draco y js-aruco2
  fonts/      *   Fraunces y Plus Jakarta Sans en woff2
  marca/      *   icono del sitio y tarjeta de 1200×630 para compartir
debug/
  banco.html        banco de trabajo: marcar, medir y exportar JSON sobre cualquier modelo
  pano-debug.html   visor de la panorámica con panel de parámetros
despliegue/   publicar.sh; el .htaccess va en la raíz
```

`*` no incluido en este repositorio (ver [Por qué faltan los assets](#por-qué-faltan-los-assets)).

El material original (los .glb de 90 MB, los JPG de cámara, el PDF de imprenta) ya no
está en el proyecto. `assets/` se basta solo: todo lo que el sitio sirve vive ahí. Las
herramientas que parten de originales —`ingesta.py` y `huella_glb.py`— leen la carpeta
que indique la variable `MV_ORIGINALES`.

### Piezas

15 en total, 10 con modelo 3D:

| código | denominación | media |
|---|---|---|
| LCDCP-MV-00004 | Punta de proyectil | 2D |
| LCDCP-MV-00005 | Bastón lítico | 2D |
| LCDCP-MV-00008 | Guijarro con surco | 3D |
| LCDCP-MV-00011 | Preforma o matriz bifacial de cuarzo | 2D |
| LCDCP-MV-00152 | Punta de proyectil pedunculada | 2D |
| LCDCP-MV-00171 | Punzón, fragmento | 2D |
| LCDCP-MV-00200 | Raedera bifacial | 3D |
| LCDCP-MV-01377 | Yesquero | 2D |
| LCDCP-MV-01821 | Nudos | 3D |
| LCDCP-MV-01892 | Molar | 2D |
| LCDCP-MV-01898 | Colmillo | 2D |
| LCDCP-MV-01934 | Escápula | 2D |
| LCDCP-MV-02112 | Colmillo | 2D |
| LCDCP-MV-02115 | Huella | 3D |
| LCDCP-MV-01894 | Ilion | 2D |

`assets/data/catalogo.json` las consolida con rutas a su media y un bloque `ar` vacío
para asociar cada pieza a su marcador.

---

## Preparación de insumos

Queda documentado cómo se derivó cada cosa, por si hay que rehacerlo con originales
nuevos. Los de la primera tanda ya no están en el proyecto.

```bash
export MV_ORIGINALES=/ruta/a/los/originales   # con 3D/ adentro
```

### Imágenes

45 MB → 9.5 MB, resolución original intacta.

```bash
magick "$MV_ORIGINALES/../IMAGENES/PIEZA.jpg" -quality 85 -define webp:method=6 assets/images/PIEZA.webp
magick assets/images/PIEZA.webp -resize "1600x1600>" -quality 80 assets/images/mobile/PIEZA.webp
```

### Modelos 3D

349 MB → 34 MB. Draco, texturas JPEG, geometría sin simplificar.

```bash
npx @gltf-transform/cli@4.5.0 jpeg ORIGEN.glb tmp.glb --quality 85
npx @gltf-transform/cli@4.5.0 optimize tmp.glb assets/models/PIEZA.glb \
  --compress draco --texture-compress false --simplify false
```

Versión móvil (texturas 1024, 5 % de la malla, 214 KB – 1.3 MB):

```bash
npx @gltf-transform/cli@4.5.0 optimize tmp.glb assets/models/mobile/PIEZA.glb \
  --compress draco --texture-compress webp --texture-size 1024 \
  --simplify true --simplify-ratio 0.05 --simplify-error 0.005
```

**No usar `EXT_texture_webp` en los modelos de escritorio.** Va en `extensionsRequired`,
así que un visor que no la soporte rechaza el archivo entero (Blender < 4.0, Visor 3D de
Windows, Quick Look). Con Draco solo, abren en Blender, three.js y `<model-viewer>`.

`LCDCP-MV-02115` llegó como STL binario: sin UV, sin material, sin color. Se convirtió a
GLB con un script propio (vértices soldados 1.39 M tris → 701 k verts, normales promediadas,
centrado y escalado a bbox unitaria, material PBR neutro). Por eso es el único que se ve gris.

### Carga en web

Todos los modelos requieren `KHR_draco_mesh_compression`, y el decodificador está
servido desde el propio sitio:

```js
const draco = new DRACOLoader().setDecoderPath('assets/vendor/three/addons/libs/draco/');
const loader = new GLTFLoader().setDRACOLoader(draco);
```

`<model-viewer>` trae su propio DRACOLoader pero, si no se le dice nada, se baja el
decodificador de `gstatic.com`. En `pieza.html` se le apunta al local:

```js
ModelViewerElement.dracoDecoderLocation = 'assets/vendor/three/addons/libs/draco/';
```

### Catálogo paginado

65 páginas a 150 dpi (1300×1182), webp q82 — 6.8 MB en total, ~100 KB por página, con
miniaturas de 260 px para la tira de navegación. El número de páginas sale siempre de
`assets/data/catalogo-paginas.json`: no se escribe a mano en ninguna página.

Desde septiembre de 2026 el PDF viene en **pliegos**: la portada (folio 1) y la
contraportada (68) sueltas, y entre medio 33 pliegos con dos folios cada uno (2-3, 4-5 …
66-67). Cada pliego se corta por la mitad, así cada imagen vuelve a ser un folio y el
número que guarda cada pieza (`pagina`) es el impreso en el catálogo. Los folios 2, 6 y
67 van en blanco y quedan fuera (`vacias` del manifiesto).

```bash
pdftoppm -r 150 -jpeg -jpegopt quality=92 catalogo-monte-verde.pdf tmp/pl
# pl-01 y pl-35: una página; pl-02 … pl-34: cortar en dos mitades → folios 2k-2 y 2k-1
for f in tmp/p-*.png; do n=$(basename "$f" .png)
  magick "$f" -quality 82 -define webp:method=6 "assets/catalogo/paginas/$n.webp"
  magick "$f" -resize 260x -quality 72 "assets/catalogo/thumbs/$n.webp"
done
```

Las páginas, miniaturas y el PDF se piden con `?v=N` (la `V` de `catalogo.html`, que
`tools/version.py` mantiene): se cachean un año y, si el catálogo cambia, tienen que
llegar las nuevas aunque se llamen igual. Después de reemplazarlas, correr `version.py`.

`catalogo.html` acepta `?p=N`, precarga las páginas vecinas, navega con flechas del teclado,
deslizamiento táctil y clic en los bordes de la hoja. La ficha de cada pieza enlaza a su
página del catálogo.

Las miniaturas llevan `aspect-ratio` en CSS: sin eso, al ser `loading="lazy"` no tienen
tamaño hasta cargarse y la tira no puede centrarse en la página activa.

---

## Panorámica del sitio

`assets/pano/sitio-360-4k.webp` — equirectangular 360×180, sintética. La costura cierra
(diferencia en el borde 2.12 vs 1.90 entre columnas vecinas normales).

El problema: **el contenido real ocupa solo 80.7° × 53.8°**, el 6.7 % de los píxeles. El
resto es relleno generado, y al hacer zoom se deshace.

`assets/pano/parche-real.webp` es la foto aérea real reproyectada sobre esa ventana, a
2× la resolución del equirect (3508×2280). Se ubicó por emparejamiento SIFT + homografía
contra la panorámica, con el borde desvanecido para que no se note el empalme.

Caja del parche en el equirect de 7680×3840: `x 3029..4783, y 1762..2902`.

### Techo de resolución

La foto real viene del PDF de imprenta (3421 px). Eso da **41.6 px por grado**, y el 1:1
con el píxel de pantalla cae en **fov 38°** (teléfono vertical y escritorio 16:9 por igual).
Más zoom que eso es interpolar.

| fov | detalle | giro ± (teléfono vertical) |
|---|---|---|
| 53° | 1.50x | 28° |
| 45° | 1.25x | 30° |
| **38°** | **1.04x ← 1:1** | **32°** |
| 30° | 0.81x | 34° |

Con el archivo original del dron ese techo se corre y hay que rehacer el parche y la tabla.

### Configuración fijada

```json
{
  "fovInicial": 23, "fovMin": 23, "fovMax": 45,
  "pitchMin": -46, "pitchMax": 7,
  "yawInicial": 87.4, "yawLimitado": true, "yawRango": 40,
  "sensibilidad": 0.15, "inercia": 0.88, "autoGiro": 0
}
```

Vive en la constante `CONFIG` de `debug/pano-debug.html`. Pendiente: `pitchMax: 7` con
fov 23 deja ver hasta +18.5°, o sea por encima del borde de la foto, donde se nota la
banda de empalme con el cielo. Bajarlo a −4 lo oculta.

---

## Huella (LCDCP-MV-02115)

`huella.html` es la estación pública: el modelo en 3D con tres capas de visualización
—**relieve** (sin textura, con luz rasante), **textura real** del escaneo y **nube de
puntos**—, más el contorno marcado por el equipo. El dedo gira la pieza; la luz se mueve
inclinando el teléfono (sensor de orientación) o con la rueda que aparece en pantallas sin
sensor. Un botón saca el molde en su propia escena.

En pantalla sólo se muestra texto de la ficha del catálogo. Las mediciones derivadas del
modelo quedan en `assets/data/huella-contorno.json` como material de trabajo y no se
publican.

El modelo lo entregó diseño recortado y texturizado. Al integrarlo hubo que: quitarle una
rotación de +90° en X (dejaba la altura en Z), escalarlo de milímetros a metros, corregir
el balance de blancos de la textura (venía con R/B = 0.63, un azul fuerte), quitar 25
reflejos especulares del escáner y bajar el atlas de 4096 a 2048 y 1024. El contorno
marcado sobre la malla anterior se recuperó por correlación entre los dos mapas de altura
(0.966, desplazamiento de 30.3 × 15.4 mm).


`visor.html?id=LCDCP-MV-02115` lee el relieve del bloque escaneado desde un mapa de altura de
1024×1198 extraído del STL (`assets/data/huella-altura.{png,json}`: 16 bits en los
canales R/G, máscara en B). No carga la malla de 1.39 M triángulos, así que corre
fluido en teléfono.

Tres modos: **luz rasante** con dirección y altura regulables, **profundidad** en mm
bajo el plano ajustado al bloque, y **positivo** (el hueco invertido en bulto).
Arrastrando sobre la imagen se traza un corte transversal con su perfil y medidas.

**El signo del relieve está fijado y no se cambia.** Con el signo base la huella se lee
como la depresión que es y se distinguen los dedos; con el opuesto aparece como un bulto
y confunde — verificado contra la pieza. El botón "invertir relieve" queda sólo para
comparar. La luz arranca desde arriba-izquierda (135°), que es la convención con la que
el ojo lee huecos como huecos.

Dos hechos de la malla, medidos:

- Es una **superficie abierta**, no un sólido: la separación mediana entre su cara
  superior e inferior es 0.0 mm. No hay "cara oculta"; mirarla del otro lado es la misma
  piel por detrás, con el relieve invertido.
- El **68.5 %** de las normales apuntan a +Z y sólo el 1.5 % al lado opuesto, así que la
  proyección correcta es desde +Z. Los otros dos ejes dan el bloque de canto.

La depresión cae hasta **57 mm** bajo el plano del bloque y ocupa el 17 % de la superficie.
Qué parte de eso es la huella y qué es relieve del sedimento lo tiene que marcar el equipo.

---

## Visor de debug

```bash
python3 -m http.server 8080          # desde la raíz del proyecto
```

- escritorio: http://localhost:8080/debug/pano-debug.html
- teléfono (misma wifi): `http://<ip-lan>:8080/debug/pano-debug.html`

Arranca solo en modo real. El HUD informa `yaw`, `pitch`, `fov`, `fps`, `detalle` (1.00x =
píxel nativo) y `viendo` (FOTO REAL / SINTÉTICO / BORDE).

Barra inferior:

| botón | qué hace |
|---|---|
| modo real | encuadra el parche, enciende cielo sintético y limita el recorrido a la foto |
| fijar zoom | clava el fov actual y calcula los límites que quedan |
| grabar | grabás moviéndote libre; los extremos que alcances pasan a ser los límites |
| pinchar | clic sobre el terreno → banderita (punto, línea, texto) anclada a yaw/pitch |
| copiar | JSON al portapapeles con config + banderitas |

Tecla **P** alterna el parche real para comparar contra el sintético.

Las banderitas se esconden al moverse y reaparecen 180 ms después de frenar. El nombre se
edita en la lista del panel; `→` viaja al punto, `×` lo borra.

---

## Marcadores

Se usan **ArUco**, no marcadores de imagen: el tracking no depende del diseño del panel y
no hay que validar arte antes de imprimir.

Se usa **`DICT_4X4_100`**: las 15 placas toman los IDs 0–14 y las caras de los cubos
llegan hasta el 79, así que `DICT_4X4_50` no alcanza. `tools/impresos.py` genera con ese
diccionario y lo deja anotado en `marcadores.json`; el navegador detecta con js-aruco2
`ARUCO_4X4_1000`, que lo contiene.

```python
import cv2.aruco as aruco
d = aruco.getPredefinedDictionary(aruco.DICT_4X4_100)
cv2.imwrite(f'marker_{i:02d}.png', aruco.generateImageMarker(d, i, 600))
```

Tamaño de impresión: detecta hasta ~7× su lado con margen por luz de sala. 25 cm cubre a
alguien parado frente al panel (~1.75 m). Requiere borde blanco propio de ≥ 1 módulo (≈3.5 cm)
o no detecta, por grande que sea.

Anclado y mano son dos modos con un botón, no simultáneos: ArUco y MediaPipe Hands sobre el
mismo frame tiran los fps al piso en gama media.

---

## Requisitos de despliegue

**HTTPS obligatorio.** Cámara (`getUserMedia`) y giroscopio (`DeviceOrientationEvent`) están
bloqueados fuera de contexto seguro. En HTTP no funciona ni el AR ni la panorámica con
giroscopio. En iOS el giroscopio además exige `DeviceOrientationEvent.requestPermission()`
disparado por un gesto del usuario.

Para probar por LAN en HTTP: en Chrome del teléfono, `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
→ agregar el origen → relanzar.

Hosting: servidor propio, estático. Nada que instalar: no hay build ni dependencias de red.

### Cabeceras

El esquema de versiones de `tools/version.py` sólo rinde si el servidor cachea largo lo
que lleva `?v=N` y revalida el HTML. **La `<meta http-equiv="cache-control">` del HTML no
sirve**: los navegadores sólo hacen caso a las cabeceras HTTP reales.

El sitio corre en Apache y las pone el `.htaccess` de la raíz. Hubo copias para nginx y
Netlify, pero se borraron: nadie las usaba y cada cambio había que repetirlo en tres lados.

Trae además los tipos MIME de `glb`, `webp`, `woff2` y `wasm`, el `404.html` y, en
Apache, la redirección a HTTPS.

### Módulos de ar.html y visor.html

Cada página importa **todos** sus módulos directamente, con `?v=N`, y los módulos no
se importan entre sí (salvo three.js, que es de `vendor/`). No es un descuido: los `.js`
se cachean un año y `tools/version.py` sólo actualiza el `?v=N` del HTML. Un
`import './otro.js'` dentro de un módulo quedaría sin versión y el teléfono lo seguiría
usando viejo. Lo que un módulo necesita de otro se lo pasa la página como parámetro.

### Sin conexión

`sw.js` (el service worker, registrado desde `assets/js/offline.js`) guarda el sitio
en el teléfono para que la ruta siga andando cuando se cae la señal. Al instalarse baja
las páginas, el código y el 360; una vez cargada la página, las fotos móviles, los
modelos móviles y las miniaturas del catálogo (~12 MB en total; con ahorro de datos,
sin modelos).

- **HTML y `assets/data/*.json`**: primero la red; lo guardado sólo si no contesta en
  3,5 s. Los cambios llegan solos.
- **Todo lo demás**: primero lo guardado. Un cambio en CSS, JS, fotos o modelos
  **sólo llega corriendo `tools/version.py`**: la versión nueva registra un service
  worker nuevo, que baja todo de nuevo y borra el caché anterior.
- No toca `analitica/`, `assets/impresos/`, los PDF ni los modelos de escritorio.

En localhost y en IPs locales está apagado para que al editar se vea lo último. Para
probarlo: `localStorage.setItem('mv:offline', '1')` en la consola y recargar.

### Qué se sube

La carpeta del proyecto no es el sitio: también tiene el repositorio, las herramientas y
esta documentación. **El riesgo serio es `.git`**: si la raíz web es esta carpeta,
`/.git/config` se lee y con eso se reconstruye el repositorio entero, historia incluida.

```bash
./despliegue/publicar.sh usuario@servidor:/var/www/monteverde/
./despliegue/publicar.sh --prueba usuario@servidor:/var/www/monteverde/   # sin escribir
```

Deja fuera `.git`, `tools/`, `despliegue/`, los originales y el README. El `.htaccess` sí
viaja: es el que pone las cabeceras.

El `.htaccess` trae además negaciones y `Options -Indexes`, pero
eso es la red de seguridad, no la primera defensa: **si el hosting tiene
`AllowOverride None`, Apache ignora el `.htaccess` completo y no avisa**. Lo que no se
copia no se puede pedir.

`debug/` sí se publica a propósito: la portada lo enlaza mientras se ajusta el paseo.
Cuando la ruta se inaugure, hay que sacar esa sección y excluir la carpeta.

---

## Herramientas

ImageMagick · `@gltf-transform/cli@4.5.0` · OpenCV (venv) · poppler-utils

Servidas desde el sitio, en `assets/vendor/`: three.js 0.180 · `@google/model-viewer` 4.0.0 ·
js-aruco2 2.0.0 · decodificador Draco.

Para actualizar alguna, se baja la versión nueva a su carpeta de `assets/vendor/` y se
revisa que no haya quedado ningún `import` relativo apuntando fuera. `three.module.js`,
por ejemplo, reexporta desde `three.core.js`: hay que bajar los dos.

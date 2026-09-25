<?php
// Libro de visitas (libro.html).
//
//   GET   los mensajes publicados, del más nuevo al más viejo
//   POST  un mensaje nuevo; queda pendiente hasta que se publica desde el panel
//
// Nada de lo que escribe un visitante se ve sin pasar por el panel: el sitio es de un
// proyecto público y un libro abierto se llena de publicidad en una semana.
declare(strict_types=1);
require __DIR__ . '/comun.php';
configuracion();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-cache');
header('X-Robots-Tag: noindex');

// Sin nombre ni contacto: para recolectar datos personales hay que verlo antes con jurídica.
const MAX_LUGAR = 60, MAX_MENSAJE = 600;
const POR_DIA = 3;                   // mensajes por persona y día
const TOPE_PENDIENTES = 300;         // si nadie modera, el archivo no crece sin fin
const MOSTRAR = 200;

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $publicados = array_values(array_filter(leer_libro(), function ($m) { return $m['estado'] === 'publicado'; }));
    $publicados = array_reverse($publicados);
    responder(200, array_map(function ($m) {
        // sin nombre aunque un mensaje viejo lo tenga: no se publican datos personales
        return ['fecha' => substr($m['fecha'], 0, 10), 'lugar' => $m['lugar'], 'mensaje' => $m['mensaje']];
    }, array_slice($publicados, 0, MOSTRAR)));
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') responder(405, ['error' => 'Sólo GET o POST.']);

$d = json_decode((string) file_get_contents('php://input', false, null, 0, 8192), true);
if (!is_array($d)) responder(400, ['error' => 'No llegó el mensaje.']);

// Trampas para robots: un campo que la persona no ve y el tiempo desde que se abrió la
// página. A quien cae se le dice que salió bien, para que no insista con otra cosa.
if (!empty($d['web']) || (int) ($d['ms'] ?? 0) < 3000) responder(200, ['ok' => true]);

$lugar = linea($d['lugar'] ?? '', MAX_LUGAR);
// el mensaje puede tener saltos de línea, pero no una pared de ellos
$mensaje = is_string($d['mensaje'] ?? null) ? $d['mensaje'] : '';
$mensaje = preg_replace('/[\x00-\x09\x0B-\x1F\x7F]+/u', ' ', str_replace("\r", '', $mensaje)) ?? '';
$mensaje = trim(preg_replace('/\n{3,}/', "\n\n", $mensaje) ?? '');
$mensaje = mb_substr($mensaje, 0, MAX_MENSAJE);

if (mb_strlen($mensaje) < 3) responder(400, ['error' => 'Escribe un mensaje.']);
if (preg_match('~(https?://|www\.|\.(com|cl|net|org)\b)~i', $lugar . ' ' . $mensaje))
    responder(400, ['error' => 'Sin enlaces, por favor: el libro es para mensajes.']);

$quien = visitante();
$libro = leer_libro();
$hoy = date('Y-m-d');
$suyos = 0;
$pendientes = 0;
foreach ($libro as $m) {
    if (($m['visitante'] ?? '') === $quien && strncmp($m['fecha'], $hoy, 10) === 0) $suyos++;
    if ($m['estado'] === 'pendiente') $pendientes++;
}
if ($suyos >= POR_DIA) responder(429, ['error' => 'Ya firmaste varias veces hoy. ¡Gracias!']);
if ($pendientes >= TOPE_PENDIENTES) responder(503, ['error' => 'El libro está lleno por hoy. Prueba mañana.']);

sumar_al_libro([
    'id' => bin2hex(random_bytes(6)),
    'fecha' => date('Y-m-d H:i'),
    'lugar' => $lugar,
    'mensaje' => $mensaje,
    'estado' => 'pendiente',
    'visitante' => $quien,
]);
responder(200, ['ok' => true]);

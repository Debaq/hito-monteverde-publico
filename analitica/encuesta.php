<?php
// Recibe las respuestas de la consulta (encuesta.html) y las guarda en
// datos/encuesta.jsonl.php. Sólo POST: lo respondido se mira en el panel.
//
// No pide datos personales (para eso hay que verlo antes con jurídica). Igual no se
// publica en ninguna parte: se lee con la clave
// del panel y de ahí se baja en CSV.
declare(strict_types=1);
require __DIR__ . '/comun.php';
require __DIR__ . '/preguntas.php';
configuracion();

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');

const POR_DIA = 5;            // respuestas por persona y día: en la visita a veces se comparte el teléfono
const TOPE_BYTES_ENCUESTA = 20 * 1024 * 1024;

if ($_SERVER['REQUEST_METHOD'] !== 'POST') responder(405, ['error' => 'Sólo POST.']);

$d = json_decode((string) file_get_contents('php://input', false, null, 0, 16384), true);
if (!is_array($d)) responder(400, ['error' => 'No llegaron las respuestas.']);

// Las mismas trampas del libro de visitas: el campo que la persona no ve y el tiempo
// desde que abrió la página. A quien cae se le dice que salió bien.
if (!empty($d['web']) || (int) ($d['ms'] ?? 0) < 8000) responder(200, ['ok' => true]);

$r = ['fecha' => date('Y-m-d H:i'), 'visitante' => visitante()];

$faltan = [];
foreach (PREGUNTAS as $k => [$tipo, $texto, $opciones, $obligatoria]) {
    $v = $d[$k] ?? null;
    switch ($tipo) {
        case 'una':
            $v = is_string($v) && isset($opciones[$v]) ? $v : '';
            break;
        case 'varias':
            $v = is_array($v) ? array_values(array_unique(array_filter($v, function ($x) use ($opciones) {
                return is_string($x) && isset($opciones[$x]);
            }))) : [];
            break;
        case 'nota':
            $v = is_numeric($v) && (int) $v >= 1 && (int) $v <= 5 ? (int) $v : null;
            break;
        case 'texto':
            $v = linea($v, 160);
            break;
        case 'palabras':
            $v = is_array($v) ? array_values(array_filter(array_map(function ($x) { return linea($x, 40); },
                                                                     array_slice($v, 0, 3)))) : [];
            break;
    }
    if ($obligatoria && ($v === '' || $v === null || $v === [])) $faltan[] = $texto;
    $r[$k] = $v;
}
if ($faltan) {
    preg_match('/^(\d+)\./', $faltan[0], $m);
    responder(400, ['error' => 'Falta responder la pregunta ' . ($m[1] ?? '') . '.', 'faltan' => count($faltan)]);
}

$quien = $r['visitante'];
$hoy = date('Y-m-d');
$suyas = 0;
foreach (leer_jsonl(ENCUESTA) as $x)
    if (($x['visitante'] ?? '') === $quien && strncmp($x['fecha'] ?? '', $hoy, 10) === 0) $suyas++;
if ($suyas >= POR_DIA) responder(429, ['error' => 'Ya se respondieron varias encuestas desde este teléfono hoy. ¡Gracias!']);
if (is_file(ENCUESTA) && filesize(ENCUESTA) > TOPE_BYTES_ENCUESTA) responder(503, ['error' => 'No se pudo guardar. Prueba más tarde.']);

sumar_jsonl(ENCUESTA, $r);
responder(200, ['ok' => true]);

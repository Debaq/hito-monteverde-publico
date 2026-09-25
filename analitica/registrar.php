<?php
// Anota un evento que manda assets/js/analitica.js.
//
// Sin cookies y sin guardar la IP: el visitante es un hash de IP + navegador + una sal
// que cambia cada día. Alcanza para contar personas distintas en un día y no permite
// seguir a nadie de un día a otro.
declare(strict_types=1);
require __DIR__ . '/comun.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit; }
// Respuesta vacía siempre: a quien manda basura no se le dice qué estuvo mal.
http_response_code(204);

$ua = $_SERVER['HTTP_USER_AGENT'] ?? '';
if ($ua === '' || preg_match('/bot|crawl|spider|slurp|preview|headless|lighthouse/i', $ua)) exit;

$d = json_decode((string) file_get_contents('php://input', false, null, 0, 2048), true);
if (!is_array($d)) exit;

$evento = $d['evento'] ?? '';
$pagina = $d['pagina'] ?? '';
if (!in_array($evento, EVENTOS, true) || !in_array($pagina, PAGINAS, true)) exit;

$texto = fn($v, $patron) => is_string($v) && preg_match($patron, $v) ? $v : '';
$pieza   = $texto($d['pieza'] ?? null,   '/^LCDCP-MV-\d{5}$/');
$entrada = $texto($d['entrada'] ?? null, '/^[a-z0-9.\-]{1,60}$/');
$detalle = $texto($d['detalle'] ?? null, '/^[A-Za-z0-9_.\-]{1,40}$/');

if (preg_match('/iPhone|iPad|iPod/', $ua))  $sistema = 'ios';
elseif (preg_match('/Android/', $ua))       $sistema = 'android';
else                                        $sistema = 'otro';

configuracion();
$visitante = visitante();

$ruta = archivo_mes(date('Y-m'));
if (is_file($ruta) && filesize($ruta) > TOPE_BYTES) exit;
if (!is_dir(DATOS)) mkdir(DATOS, 0750, true);
if (!is_file($ruta)) file_put_contents($ruta, GUARDA, LOCK_EX);

$fila = [date('Y-m-d H:i:s'), $visitante, $evento, $pagina, $pieza, $entrada, $sistema, $detalle];
file_put_contents($ruta, implode(',', $fila) . "\n", FILE_APPEND | LOCK_EX);

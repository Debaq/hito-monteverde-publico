<?php
// Lo que comparten el registro y el panel: dónde viven los datos y qué se acepta.
declare(strict_types=1);
// El hosting corre PHP 7.4: nada de match, str_starts_with ni otras cosas de PHP 8.

date_default_timezone_set('America/Santiago');

const DATOS = __DIR__ . '/datos';

// Cada archivo de datos termina en .php y abre con esta línea: si alguna vez el
// servidor ignora el .htaccess de datos/, pedirlo ejecuta PHP y no entrega nada.
const GUARDA = "<?php http_response_code(404); exit; ?>\n";

// Sólo esto se anota. Lo demás se descarta sin avisar: el registro está abierto a
// cualquiera, así que nada de lo que llega se escribe sin pasar por aquí.
const EVENTOS = ['vista', 'ar_pieza', 'ar_camara', 'foto'];
const PAGINAS = ['index.html', 'catalogo.html', 'pieza.html', 'visor.html', 'panorama.html', 'ar.html',
                 'libro.html', 'encuesta.html'];
const COLUMNAS = ['fecha', 'visitante', 'evento', 'pagina', 'pieza', 'entrada', 'sistema', 'detalle'];

// Un mes normal son unos pocos MB. Si alguien se pone a llenar el disco, se corta aquí.
const TOPE_BYTES = 50 * 1024 * 1024;

function configuracion(): void {
    if (!is_file(__DIR__ . '/config.php')) {
        http_response_code(500);
        exit('Falta analitica/config.php: copia config.ejemplo.php y completa la clave y la sal.');
    }
    require_once __DIR__ . '/config.php';
}

function archivo_mes(string $mes): string {
    return DATOS . "/$mes.csv.php";
}

/** Filas de un mes como arreglos asociativos. $mes es AAAA-MM. */
function leer_mes(string $mes): array {
    $ruta = archivo_mes($mes);
    if (!is_file($ruta)) return [];
    $filas = [];
    foreach (file($ruta, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $linea) {
        if (strncmp($linea, '<?php', 5) === 0) continue;
        $campos = explode(',', $linea);
        if (count($campos) !== count(COLUMNAS)) continue;
        $filas[] = array_combine(COLUMNAS, $campos);
    }
    return $filas;
}

function meses_con_datos(): array {
    $meses = [];
    foreach (glob(DATOS . '/*.csv.php') ?: [] as $ruta)
        $meses[] = basename($ruta, '.csv.php');
    rsort($meses);
    return $meses;
}

/**
 * Quién es, sin saber quién es: un hash de IP + navegador + una sal que cambia cada día.
 * Alcanza para contar personas distintas en un día y no permite seguir a nadie de un
 * día a otro. La IP no se guarda.
 */
function visitante(): string {
    return substr(hash('sha256', date('Y-m-d') . SAL . ($_SERVER['REMOTE_ADDR'] ?? '')
                                 . ($_SERVER['HTTP_USER_AGENT'] ?? '')), 0, 12);
}

// ---------- archivos de registros: el libro de visitas y la encuesta
// Un registro por línea, en JSON, con la misma línea de guarda que los datos de visitas.
const LIBRO = DATOS . '/libro.jsonl.php';        // estados: pendiente, publicado, oculto
const ENCUESTA = DATOS . '/encuesta.jsonl.php';

function leer_jsonl(string $ruta): array {
    if (!is_file($ruta)) return [];
    $registros = [];
    foreach (file($ruta, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $linea) {
        if (strncmp($linea, '<?php', 5) === 0) continue;
        $r = json_decode($linea, true);
        if (is_array($r)) $registros[] = $r;
    }
    return $registros;
}

function sumar_jsonl(string $ruta, array $r): void {
    if (!is_dir(DATOS)) mkdir(DATOS, 0750, true);
    if (!is_file($ruta)) file_put_contents($ruta, GUARDA, LOCK_EX);
    file_put_contents($ruta, json_encode($r, JSON_UNESCAPED_UNICODE) . "\n", FILE_APPEND | LOCK_EX);
}

/**
 * Para moderar: `$cambio` recibe cada registro y devuelve el registro cambiado, o null
 * para borrarlo. Todo bajo el mismo candado que usa sumar_jsonl, para que uno que llega
 * mientras se modera no se pierda al reescribir.
 */
function modificar_jsonl(string $ruta, callable $cambio): void {
    if (!is_file($ruta)) return;
    $f = fopen($ruta, 'c+');
    if (!$f || !flock($f, LOCK_EX)) return;
    $txt = GUARDA;
    foreach (explode("\n", stream_get_contents($f)) as $linea) {
        if ($linea === '' || strncmp($linea, '<?php', 5) === 0) continue;
        $r = json_decode($linea, true);
        if (!is_array($r)) continue;
        $r = $cambio($r);
        if ($r !== null) $txt .= json_encode($r, JSON_UNESCAPED_UNICODE) . "\n";
    }
    ftruncate($f, 0);
    rewind($f);
    fwrite($f, $txt);
    fflush($f);
    flock($f, LOCK_UN);
    fclose($f);
}

function leer_libro(): array {
    return array_values(array_filter(leer_jsonl(LIBRO), function ($m) { return isset($m['id']); }));
}
function sumar_al_libro(array $m): void { sumar_jsonl(LIBRO, $m); }
function modificar_libro(callable $cambio): void { modificar_jsonl(LIBRO, $cambio); }

// ---------- para los formularios públicos (libro y encuesta)
function responder(int $codigo, array $datos): void {
    http_response_code($codigo);
    echo json_encode($datos, JSON_UNESCAPED_UNICODE);
    exit;
}

/** Texto de una línea: sin caracteres de control ni espacios de más. */
function linea($v, int $max): string {
    $v = is_string($v) ? $v : '';
    $v = preg_replace('/[\x00-\x1F\x7F]+/u', ' ', $v) ?? '';
    $v = trim(preg_replace('/\s+/u', ' ', $v) ?? '');
    return mb_substr($v, 0, $max);
}

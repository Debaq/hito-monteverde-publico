<?php
// Panel de visitas. Protegido con la clave de config.php.
declare(strict_types=1);
require __DIR__ . '/comun.php';
require __DIR__ . '/preguntas.php';
configuracion();

session_name('mvpanel');
session_set_cookie_params(['httponly' => true, 'secure' => !empty($_SERVER['HTTPS']), 'samesite' => 'Strict']);
session_start();
header('X-Robots-Tag: noindex, nofollow');

if (isset($_POST['salir'])) { $_SESSION = []; session_destroy(); header('Location: ./'); exit; }

$error = '';
if (isset($_POST['clave'])) {
    if (CLAVE_HASH !== '' && password_verify((string) $_POST['clave'], CLAVE_HASH)) {
        session_regenerate_id(true);
        $_SESSION['ok'] = true;
        header('Location: ./');
        exit;
    }
    sleep(1);                                  // probar claves a mano cuesta
    $error = 'Clave incorrecta.';
}

$h = fn($s) => htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8');

if (empty($_SESSION['ok'])) { ?>
<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Visitas — Monte Verde</title>
<style>
  body { font: 16px/1.4 system-ui, sans-serif; background: #16110C; color: #EDE3D2;
         display: grid; place-items: center; min-height: 100vh; margin: 0; }
  form { display: grid; gap: .6rem; width: min(280px, 90vw); }
  input, button { font: inherit; padding: .6rem .8rem; border-radius: 8px; border: 1px solid #5a4a38; }
  input { background: #221a12; color: inherit; }
  button { background: #C8894B; color: #16110C; border: 0; cursor: pointer; }
  p { color: #e08a7a; margin: 0; }
</style>
<form method="post">
  <strong>Visitas — Monte Verde</strong>
  <input type="password" name="clave" placeholder="Clave" autofocus required>
  <button>Entrar</button>
  <?php if ($error) echo "<p>{$h($error)}</p>"; ?>
</form>
<?php exit; }

// ---------- libro de visitas: publicar, ocultar o descartar
if (!isset($_SESSION['token'])) $_SESSION['token'] = bin2hex(random_bytes(16));
if (isset($_POST['libro'], $_POST['id']) && hash_equals($_SESSION['token'], (string) ($_POST['token'] ?? ''))) {
    $accion = (string) $_POST['libro'];
    $id = (string) $_POST['id'];
    modificar_libro(function ($m) use ($accion, $id) {
        if ($m['id'] !== $id) return $m;
        if ($accion === 'descartar') return null;
        if ($accion === 'publicar') $m['estado'] = 'publicado';
        if ($accion === 'ocultar') $m['estado'] = 'oculto';
        return $m;
    });
    header('Location: ./' . (isset($_GET['mes']) ? '?mes=' . rawurlencode((string) $_GET['mes']) : '') . '#libro');
    exit;
}
$libro = array_reverse(leer_libro());
$porModerar = array_filter($libro, function ($m) { return $m['estado'] === 'pendiente'; });
$moderados = array_slice(array_values(array_filter($libro, function ($m) { return $m['estado'] !== 'pendiente'; })), 0, 30);

// ---------- descarga del mes en CSV, para abrirlo en una planilla
$meses = meses_con_datos();
$mes = isset($_GET['mes']) && in_array($_GET['mes'], $meses, true) ? $_GET['mes'] : ($meses[0] ?? date('Y-m'));
$filas = leer_mes($mes);

// ---------- encuesta: todas las respuestas en CSV
$encuesta = leer_jsonl(ENCUESTA);
if (isset($_GET['encuesta_csv'])) {
    header('Content-Type: text/csv; charset=utf-8');
    header('Content-Disposition: attachment; filename="encuesta-monte-verde-' . date('Y-m-d') . '.csv"');
    $salida = fopen('php://output', 'w');
    fwrite($salida, "\xEF\xBB\xBF");                 // BOM: Excel lee bien las tildes
    $columnas = array_merge(['fecha'], array_keys(PREGUNTAS));
    fputcsv($salida, array_merge(['Fecha'], array_map(function ($p) { return $p[1]; }, PREGUNTAS)));
    foreach ($encuesta as $x) {
        $fila = [];
        foreach ($columnas as $k) {
            $v = $x[$k] ?? '';
            if (is_array($v)) {                      // opciones marcadas: por su etiqueta
                $ops = PREGUNTAS[$k][2] ?? null;
                $v = implode('; ', array_map(function ($o) use ($ops) { return $ops[$o] ?? $o; }, $v));
            } elseif (isset(PREGUNTAS[$k]) && PREGUNTAS[$k][0] === 'una') {
                $v = PREGUNTAS[$k][2][$v] ?? $v;
            }
            $fila[] = $v;
        }
        fputcsv($salida, $fila);
    }
    exit;
}

if (isset($_GET['descargar'])) {
    header('Content-Type: text/csv; charset=utf-8');
    header("Content-Disposition: attachment; filename=\"visitas-$mes.csv\"");
    echo implode(',', COLUMNAS), "\n";
    foreach ($filas as $f) echo implode(',', $f), "\n";
    exit;
}

// ---------- cuentas
// El visitante cambia cada día, así que "personas" es siempre por día: una misma
// persona que vuelve el martes cuenta otra vez.
$nombres = [];
$cat = json_decode((string) @file_get_contents(__DIR__ . '/../assets/data/catalogo.json'), true);
foreach ($cat['piezas'] ?? [] as $p) $nombres[$p['codigo']] = $p['denominacion'] ?? $p['codigo'];

$personas = $porDia = $porPagina = $porPieza = $entradas = $sistemas = $camara = $fotos = [];
$vistas = 0;
foreach ($filas as $f) {
    $dia = substr($f['fecha'], 0, 10);
    $quien = "$dia|{$f['visitante']}";
    $personas[$quien] = $f['sistema'];
    $porDia[$dia]['personas'][$quien] = 1;
    $porDia[$dia] += ['vistas' => 0, 'directas' => 0, 'ar' => 0];

    if ($f['evento'] === 'vista') {
        $vistas++;
        $porDia[$dia]['vistas']++;
        $porPagina[$f['pagina']]['vistas'] = ($porPagina[$f['pagina']]['vistas'] ?? 0) + 1;
        $porPagina[$f['pagina']]['personas'][$quien] = 1;
        if ($f['entrada'] === 'directa') $porDia[$dia]['directas']++;
        if ($f['entrada'] !== 'interna') $entradas[$f['entrada']] = ($entradas[$f['entrada']] ?? 0) + 1;
        if ($f['pieza'] !== '') {
            $col = $f['pagina'] === 'pieza.html' ? 'ficha' : ($f['pagina'] === 'visor.html' ? 'visor' : null);
            if ($col) $porPieza[$f['pieza']][$col] = ($porPieza[$f['pieza']][$col] ?? 0) + 1;
        }
    } elseif ($f['evento'] === 'ar_pieza' && $f['pieza'] !== '') {
        $porDia[$dia]['ar']++;
        $porPieza[$f['pieza']]['ar'] = ($porPieza[$f['pieza']]['ar'] ?? 0) + 1;
    } elseif ($f['evento'] === 'foto' && $f['pieza'] !== '') {
        $porPieza[$f['pieza']]['fotos'] = ($porPieza[$f['pieza']]['fotos'] ?? 0) + 1;
        $desde = $f['pagina'] === 'ar.html' ? 'Cámara AR' : 'Visor 3D';
        $como = strpos($f['detalle'], 'compartir') === 0 ? 'compartidas' : 'descargadas';
        $fotos[$desde][$como] = ($fotos[$desde][$como] ?? 0) + 1;
    } elseif ($f['evento'] === 'ar_camara') {
        $camara[$f['detalle']] = ($camara[$f['detalle']] ?? 0) + 1;
    }
}
foreach ($personas as $s) $sistemas[$s] = ($sistemas[$s] ?? 0) + 1;
ksort($porDia);
uasort($porPieza, fn($a, $b) => array_sum($b) <=> array_sum($a));
arsort($entradas); arsort($sistemas); arsort($camara);
uasort($porPagina, fn($a, $b) => $b['vistas'] <=> $a['vistas']);

$paginas = ['index.html' => 'Inicio', 'catalogo.html' => 'Catálogo', 'pieza.html' => 'Fichas',
            'visor.html' => 'Visor 3D', 'panorama.html' => 'Sitio 360°', 'ar.html' => 'Realidad aumentada'];
$entradaNombre = fn($e) => ['directa' => 'Directa (QR, enlace escrito o guardado)', 'ar' => 'Salto desde la cámara AR', '' => 'Sin dato'][$e] ?? $e;
$camaraNombre = fn($c) => ['ok' => 'Abrió bien', 'NotAllowedError' => 'Permiso rechazado',
    'NotFoundError' => 'Sin cámara trasera', 'NotReadableError' => 'Cámara ocupada',
    'OverconstrainedError' => 'Resolución no admitida', 'sin_camara' => 'Sin ninguna cámara'][$c] ?? $c;
?>
<!doctype html><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Visitas <?= $h($mes) ?> — Monte Verde</title>
<style>
  body { font: 15px/1.45 system-ui, sans-serif; background: #16110C; color: #EDE3D2;
         margin: 0 auto; padding: 16px; max-width: 900px; }
  header { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; justify-content: space-between; }
  h1 { font-size: 1.3rem; margin: 0; }
  h2 { font-size: 1rem; margin: 2rem 0 .5rem; color: #C8894B; }
  .cifras { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .6rem; margin-top: 1rem; }
  .cifras div { background: #221a12; border-radius: 10px; padding: .7rem .9rem; }
  .cifras b { display: block; font-size: 1.6rem; font-variant-numeric: tabular-nums; }
  .cifras span { color: #b9a88f; font-size: .85rem; }
  .tabla { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: .35rem .6rem; border-bottom: 1px solid #33281c; }
  td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; }
  th { color: #b9a88f; font-weight: 500; font-size: .85rem; }
  select, button, a.btn { font: inherit; padding: .35rem .7rem; border-radius: 8px; border: 1px solid #5a4a38;
         background: #221a12; color: inherit; text-decoration: none; cursor: pointer; }
  .nota { color: #b9a88f; font-size: .85rem; }
  .vacio { color: #b9a88f; }
  .msg { background: #221a12; border-radius: 10px; padding: .7rem .9rem; margin: .5rem 0;
         display: flex; gap: .8rem; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }
  .msg p { margin: .3rem 0 0; white-space: pre-wrap; }
  .msg .quien { color: #b9a88f; font-size: .85rem; }
  .msg.oculto { opacity: .55; }
  .msg form { display: flex; gap: .4rem; }
  .msg button.si { background: #C8894B; color: #16110C; border: 0; }
</style>

<header>
  <h1>Visitas — Monte Verde</h1>
  <div style="display:flex;gap:.4rem;flex-wrap:wrap">
    <form method="get">
      <select name="mes" onchange="this.form.submit()">
        <?php foreach ($meses ?: [$mes] as $m) printf('<option%s>%s</option>', $m === $mes ? ' selected' : '', $h($m)); ?>
      </select>
    </form>
    <a class="btn" href="?mes=<?= $h($mes) ?>&amp;descargar">Bajar CSV</a>
    <form method="post"><button name="salir" value="1">Salir</button></form>
  </div>
</header>

<?php
// una fila del libro, con sus botones
$mensaje = function ($m, $botones) use ($h, $mes) {
    $quien = ($m['lugar'] !== '' ? $h($m['lugar']) : 'Visitante') . ' · ' . $h($m['fecha']);
    echo '<div class="msg' . ($m['estado'] === 'oculto' ? ' oculto' : '') . '"><div style="flex:1;min-width:200px">'
       . "<span class=\"quien\">$quien</span><p>" . $h($m['mensaje']) . '</p></div>'
       . '<form method="post" action="./?mes=' . $h($mes) . '">'
       . '<input type="hidden" name="id" value="' . $h($m['id']) . '">'
       . '<input type="hidden" name="token" value="' . $h($_SESSION['token']) . '">';
    foreach ($botones as [$accion, $texto, $clase]) echo "<button name=\"libro\" value=\"$accion\" class=\"$clase\">$texto</button>";
    echo '</form></div>';
};
?>
<h2 id="libro">Libro de visitas<?= $porModerar ? ' · ' . count($porModerar) . ' por revisar' : '' ?></h2>
<?php
if (!$libro) echo '<p class="vacio">Nadie ha firmado todavía.</p>';
foreach ($porModerar as $m) $mensaje($m, [['publicar', 'Publicar', 'si'], ['descartar', 'Descartar', '']]);
if ($moderados) echo '<p class="nota">Ya revisados, los últimos:</p>';
foreach ($moderados as $m) $mensaje($m, $m['estado'] === 'publicado'
    ? [['ocultar', 'Ocultar', '']] : [['publicar', 'Publicar', 'si'], ['descartar', 'Borrar', '']]);
?>
<p class="nota">Nada se ve en el sitio hasta que se publica. Ocultar lo saca del sitio sin borrarlo.</p>

<h2 id="encuesta">Encuesta · <?= count($encuesta) ?> respuesta<?= count($encuesta) === 1 ? '' : 's' ?></h2>
<?php if (!$encuesta) { echo '<p class="vacio">Nadie ha respondido todavía.</p>'; } else { ?>
<p><a class="btn" href="?encuesta_csv">Bajar respuestas (CSV)</a></p>
<div class="tabla"><table>
<?php
foreach (PREGUNTAS as $k => [$tipo, $texto, $opciones]) {
    $vals = array_map(function ($x) use ($k) { return $x[$k] ?? null; }, $encuesta);
    if ($tipo === 'una' || $tipo === 'varias') {
        $cuenta = array_fill_keys(array_keys($opciones), 0);
        $respondieron = 0;
        foreach ($vals as $v) {
            foreach ((array) $v as $o) if (isset($cuenta[$o])) $cuenta[$o]++;
            if ($v !== '' && $v !== [] && $v !== null) $respondieron++;
        }
        $partes = [];
        foreach ($cuenta as $o => $n)
            $partes[] = $h($opciones[$o]) . ' <b>' . $n . '</b>'
                      . ($respondieron ? ' <span class="nota">(' . round(100 * $n / $respondieron) . ' %)</span>' : '');
        $resumen = implode(' · ', $partes);
    } elseif ($tipo === 'nota') {
        $notas = array_values(array_filter($vals, 'is_int'));
        $resumen = $notas ? 'promedio <b>' . number_format(array_sum($notas) / count($notas), 1, ',', '')
                          . '</b> <span class="nota">de ' . count($notas) . ' · '
                          . implode(' ', array_map(function ($i) use ($notas) {
                                return $i . ':' . count(array_keys($notas, $i, true)); }, range(1, 5)))
                          . '</span>' : '<span class="nota">sin respuestas</span>';
    } elseif ($tipo === 'palabras') {
        $frec = [];
        foreach ($vals as $v) foreach ((array) $v as $p) {
            $p = mb_strtolower(trim($p));
            if ($p !== '') $frec[$p] = ($frec[$p] ?? 0) + 1;
        }
        arsort($frec);
        $resumen = $frec ? implode(' · ', array_map(function ($p, $n) use ($h) {
            return $h($p) . ($n > 1 ? " <b>$n</b>" : ''); }, array_keys(array_slice($frec, 0, 30, true)),
            array_slice($frec, 0, 30, true))) : '<span class="nota">sin respuestas</span>';
    } else {                                              // texto libre: los últimos
        $textos = array_slice(array_reverse(array_values(array_filter($vals, function ($v) {
            return is_string($v) && $v !== ''; }))), 0, 12);
        $resumen = $textos ? implode('<br>', array_map($h, $textos)) : '<span class="nota">sin respuestas</span>';
    }
    echo '<tr><td style="max-width:320px">' . $h($texto) . "</td><td>$resumen</td></tr>";
}
?>
</table></div>
<?php } ?>

<h2>Visitas del mes</h2>
<?php if (!$filas) { echo '<p class="vacio">Todavía no hay visitas registradas este mes.</p>'; exit; } ?>

<div class="cifras">
  <div><b><?= count($personas) ?></b><span>personas-día</span></div>
  <div><b><?= $vistas ?></b><span>páginas vistas</span></div>
  <div><b><?= $entradas['directa'] ?? 0 ?></b><span>entradas directas (QR)</span></div>
  <div><b><?= count($porPagina['panorama.html']['personas'] ?? []) ?></b><span>llegaron al 360°</span></div>
  <div><b><?= array_sum(array_column($porPieza, 'ar')) ?></b><span>piezas vistas en AR</span></div>
  <div><b><?= array_sum(array_column($porPieza, 'fotos')) ?></b><span>fotos guardadas</span></div>
</div>
<p class="nota">Sin cookies: cada persona se reconoce sólo dentro del mismo día. Quien vuelve otro día cuenta de nuevo.</p>

<h2>Piezas</h2>
<div class="tabla"><table>
  <tr><th>Pieza</th><th class="n">Ficha</th><th class="n">Visor 3D</th><th class="n">En AR</th><th class="n">Fotos</th></tr>
  <?php foreach ($porPieza as $cod => $c) printf('<tr><td>%s <span class="nota">%s</span></td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>',
      $h($nombres[$cod] ?? $cod), $h($cod), $c['ficha'] ?? 0, $c['visor'] ?? 0, $c['ar'] ?? 0, $c['fotos'] ?? 0); ?>
</table></div>

<?php if ($fotos) { ?>
<h2>Fotos</h2>
<div class="tabla"><table>
  <tr><th>Desde</th><th class="n">Compartidas</th><th class="n">Descargadas</th></tr>
  <?php foreach ($fotos as $donde => $c) printf('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>',
      $h($donde), $c['compartidas'] ?? 0, $c['descargadas'] ?? 0); ?>
</table></div>
<p class="nota">Compartida es desde el teléfono (de ahí se guarda en la galería o se manda); descargada, desde el computador.</p>
<?php } ?>

<h2>Páginas</h2>
<div class="tabla"><table>
  <tr><th>Página</th><th class="n">Vistas</th><th class="n">Personas</th></tr>
  <?php foreach ($porPagina as $p => $c) printf('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td></tr>',
      $h($paginas[$p] ?? $p), $c['vistas'], count($c['personas'])); ?>
</table></div>

<h2>Cómo llegan</h2>
<div class="tabla"><table>
  <tr><th>Entrada</th><th class="n">Vistas</th></tr>
  <?php foreach ($entradas as $e => $n) printf('<tr><td>%s</td><td class="n">%d</td></tr>', $h($entradaNombre($e)), $n); ?>
</table></div>

<h2>Teléfonos</h2>
<div class="tabla"><table>
  <tr><th>Sistema</th><th class="n">Personas</th></tr>
  <?php foreach ($sistemas as $s => $n) printf('<tr><td>%s</td><td class="n">%d</td></tr>',
      $h(['ios' => 'iPhone / iPad', 'android' => 'Android', 'otro' => 'Computador u otro'][$s] ?? $s), $n); ?>
</table></div>

<?php if ($camara) { ?>
<h2>Cámara de realidad aumentada</h2>
<div class="tabla"><table>
  <tr><th>Resultado</th><th class="n">Veces</th></tr>
  <?php foreach ($camara as $c => $n) printf('<tr><td>%s</td><td class="n">%d</td></tr>', $h($camaraNombre($c)), $n); ?>
</table></div>
<?php } ?>

<h2>Por día</h2>
<div class="tabla"><table>
  <tr><th>Día</th><th class="n">Personas</th><th class="n">Vistas</th><th class="n">Directas</th><th class="n">AR</th></tr>
  <?php foreach ($porDia as $d => $c) printf('<tr><td>%s</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td><td class="n">%d</td></tr>',
      $h($d), count($c['personas']), $c['vistas'], $c['directas'], $c['ar']); ?>
</table></div>

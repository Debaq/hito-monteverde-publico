<?php
// Copiar como config.php y completar. config.php no entra al repositorio.
//
// CLAVE_HASH: la clave del panel, nunca en claro. Se genera con
//     php -r 'echo password_hash("la-clave", PASSWORD_DEFAULT), "\n";'
// SAL: cualquier texto largo al azar. Si cambia, el conteo de visitantes del día
// se parte en dos, nada más. Se genera con
//     php -r 'echo bin2hex(random_bytes(24)), "\n";'
const CLAVE_HASH = '';
const SAL = '';

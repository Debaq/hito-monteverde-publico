#!/usr/bin/env bash
# Sube al servidor sólo lo que es el sitio.
#
# Las reglas de .htaccess son la red de seguridad, no la primera defensa: si el
# hosting tiene AllowOverride None, Apache las ignora enteras y no te enterás. Lo
# que no se copia no se puede pedir.
#
#     ./despliegue/publicar.sh usuario@servidor:/var/www/monteverde/
#     ./despliegue/publicar.sh --prueba usuario@servidor:/var/www/monteverde/
set -euo pipefail

PRUEBA=""
if [ "${1:-}" = "--prueba" ]; then PRUEBA="--dry-run"; shift; fi

DESTINO="${1:-}"
if [ -z "$DESTINO" ]; then
  echo "falta el destino, por ejemplo  usuario@servidor:/var/www/monteverde/" >&2
  exit 1
fi

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --delete deja el servidor igual a esta copia: lo que se borró acá, se borra allá.
rsync -avz --delete $PRUEBA \
  --exclude '.git' \
  --exclude '.git*' \
  --exclude 'tools/' \
  --exclude 'despliegue/' \
  --exclude 'originales/' \
  --exclude 'INSUMOS/' \
  --exclude 'README.md' \
  --exclude '*.py' \
  --exclude '__pycache__/' \
  --exclude '*.bak' \
  --exclude '.DS_Store' \
  --exclude 'analitica/datos/*.php' \
  "$RAIZ/" "$DESTINO"

echo
echo "listo. el .htaccess sí va: viaja en la raíz y es el que pone las cabeceras."

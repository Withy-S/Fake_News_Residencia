#!/usr/bin/env bash
# Aplica a configuração nesta máquina. Uso: sudo ./apply.sh [--noop]
# --noop mostra o que mudaria sem alterar nada.
set -euo pipefail

cd "$(dirname "$0")"

puppet apply \
  --modulepath=modules \
  --hiera_config=hiera.yaml \
  "$@" \
  manifests/site.pp

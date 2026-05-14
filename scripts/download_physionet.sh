#!/usr/bin/env bash
set -euo pipefail

DESTINATION="${1:-data/raw}"
PROJECT="${PHYSIONET_PROJECT:-}"

if [[ -z "${PROJECT}" ]]; then
  echo "PHYSIONET_PROJECT is required, for example: PHYSIONET_PROJECT='project-slug/1.0.0'" >&2
  exit 1
fi

if ! command -v wget >/dev/null 2>&1; then
  echo "wget is required to download from PhysioNet." >&2
  exit 1
fi

mkdir -p "${DESTINATION}"

AUTH_ARGS=()
if [[ -n "${PHYSIONET_USERNAME:-}" ]]; then
  AUTH_ARGS+=(--user "${PHYSIONET_USERNAME}")
fi
if [[ -n "${PHYSIONET_PASSWORD:-}" ]]; then
  AUTH_ARGS+=(--password "${PHYSIONET_PASSWORD}")
fi

wget \
  --recursive \
  --no-parent \
  --continue \
  --timestamping \
  --no-host-directories \
  --cut-dirs=1 \
  --directory-prefix="${DESTINATION}" \
  "${AUTH_ARGS[@]}" \
  "https://physionet.org/files/${PROJECT}/"


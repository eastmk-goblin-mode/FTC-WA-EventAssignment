#!/usr/bin/env bash
# Build and start a self-hosted OSRM server for Washington, the fallback source for
# scripts/build_drive_matrix.py. Works on macOS (Homebrew) and on Linux / GitHub
# Codespaces (Docker, using the official ghcr.io/project-osrm/osrm-backend image).
#
# Needs about 2 GB of disk and about 5 GB of free RAM: osrm-extract peaked at 4.7 GB
# on the Washington extract. In Codespaces, use a 4-core (16 GB) machine; a 2-core
# (8 GB) machine is borderline.
#
# Usage: scripts/osrm_setup.sh            build if needed, then serve on 127.0.0.1:5055
#        OSRM_DIR=/some/path scripts/osrm_setup.sh
# Stop the server: kill "$(cat "$OSRM_DIR/routed.pid")" (macOS) or docker stop osrm-wa (Linux).
set -euo pipefail

OSRM_DIR="${OSRM_DIR:-$HOME/.cache/osrm-wa}"   # not /tmp: macOS can clear /tmp on reboot
PORT="${OSRM_PORT:-5055}"
PBF_URL="https://download.geofabrik.de/north-america/us/washington-latest.osm.pbf"
IMAGE="ghcr.io/project-osrm/osrm-backend"
mkdir -p "$OSRM_DIR"
cd "$OSRM_DIR"

if [[ "$(uname)" == "Darwin" ]]; then
  command -v osrm-routed >/dev/null || brew install osrm-backend
  PROFILE="$(brew --prefix osrm-backend)/share/osrm/profiles/car.lua"
  run() { "$@"; }
  DATA="."
else
  command -v docker >/dev/null || { echo "Docker is required on Linux. In Codespaces, add the docker-in-docker feature (see .devcontainer/devcontainer.json)."; exit 1; }
  PROFILE="/opt/car.lua"
  run() { docker run --rm -t -v "$OSRM_DIR:/data" "$IMAGE" "$@"; }
  DATA="/data"
fi

if [[ ! -f washington-latest.osm.pbf ]]; then
  echo "Downloading the Washington extract (about 365 MB)..."
  curl -fL -o washington-latest.osm.pbf "$PBF_URL"
fi

if [[ ! -f washington-latest.osrm.mldgr ]]; then
  echo "Building the routing graph (a few minutes)..."
  run osrm-extract -p "$PROFILE" "$DATA/washington-latest.osm.pbf" > extract.log 2>&1
  run osrm-partition "$DATA/washington-latest.osrm" > mld.log 2>&1
  run osrm-customize "$DATA/washington-latest.osrm" >> mld.log 2>&1
fi

echo "Starting OSRM on 127.0.0.1:$PORT ..."
if [[ "$(uname)" == "Darwin" ]]; then
  nohup osrm-routed --algorithm mld -i 127.0.0.1 -p "$PORT" --max-table-size 2000 washington-latest.osrm > routed.log 2>&1 &
  echo $! > routed.pid
else
  docker rm -f osrm-wa >/dev/null 2>&1 || true
  docker run -d --name osrm-wa -p "127.0.0.1:$PORT:5000" -v "$OSRM_DIR:/data" "$IMAGE" \
    osrm-routed --algorithm mld --max-table-size 2000 /data/washington-latest.osrm > /dev/null
fi

for _ in $(seq 1 60); do
  if curl -fs "http://127.0.0.1:$PORT/nearest/v1/driving/-122.33,47.6" > /dev/null; then
    echo "OSRM is up. Next: python3 scripts/build_drive_matrix.py --source osrm"
    exit 0
  fi
  sleep 2
done
echo "OSRM did not answer within 2 minutes. Check $OSRM_DIR/routed.log or: docker logs osrm-wa"
exit 1

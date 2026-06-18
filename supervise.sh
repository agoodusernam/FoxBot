#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

readonly SERVICE="foxbot"
readonly EXIT_SHUTDOWN=0
readonly EXIT_RESTART=42
readonly EXIT_UPDATE=43

while true; do
    docker compose up -d --build

    code=$(docker wait "${SERVICE}")
    docker compose rm -f "${SERVICE}" >/dev/null

    case "${code}" in
        "${EXIT_SHUTDOWN}")
            echo "Clean shutdown (exit ${code}); stopping supervisor."
            break
            ;;
        "${EXIT_RESTART}")
            echo "Restart requested (exit ${code}); recreating."
            ;;
        "${EXIT_UPDATE}")
            echo "Update requested (exit ${code}); pulling and rebuilding."
            git pull
            docker compose build
            ;;
        *)
            echo "Unexpected exit ${code}; recreating."
            ;;
    esac
done

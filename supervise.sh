#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

readonly SERVICE="foxbot"
readonly EXIT_SHUTDOWN=0
readonly EXIT_RESTART=42
readonly EXIT_UPDATE=43

# Build the image once up front (first run, or to pick up Dockerfile changes).
docker compose build

while true; do
    docker compose up -d

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
            echo "Update requested (exit ${code}); pulling."
            before=$(git rev-parse HEAD)
            git pull
            # Code is bind-mounted, so it is live without a rebuild.
            # Only rebuild when dependencies or the Dockerfile changed.
            if ! git diff --quiet "${before}" HEAD -- pyproject.toml uv.lock Dockerfile; then
                echo "Dependencies/Dockerfile changed; rebuilding image."
                docker compose build
            else
                echo "Code-only update; skipping rebuild."
            fi
            ;;
        *)
            echo "Unexpected exit ${code}; recreating."
            ;;
    esac
done

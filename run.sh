#!/usr/bin/env sh

set -ex
exec python -u -m ecs_service_discovery.cli "$@"

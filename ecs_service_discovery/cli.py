# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille <john@compose-x.io>

"""Console script for ecs_service_discovery."""
import argparse
import sys
from os import environ, makedirs

from compose_x_common.compose_x_common import DURATIONS_RE

from ecs_service_discovery.ecs_service_discovery import EcsServiceDiscovery

OUTPUT_DIRECTORY = environ.get("OUTPUT_DIRECTORY", "/tmp/prometheus")
PROMETHEUS_METRICS_PORT = environ.get("PROMETHEUS_METRICS_PORT", 8337)


def main():
    """Console script for ecs_service_discovery."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--output_dir", type=str, required=False, default=OUTPUT_DIRECTORY
    )
    parser.add_argument(
        "--profile",
        required=False,
        help="aws profile to use. Defaults to SDK default behaviour",
        type=str,
    )
    parser.add_argument(
        "-p",
        "--prometheus-port",
        type=int,
        default=PROMETHEUS_METRICS_PORT,
        required=False,
        dest="prometheus_port",
    )
    parser.add_argument(
        "--intervals",
        type=str,
        help="Time between ECS discovery intervals",
        default="30s",
    )
    parser.add_argument(
        "--prometheus-output-format",
        type=str,
        default="json",
        help="Change the format of generated files. JSON or YAML.",
    )
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()
    print("Arguments: " + str(args._))
    try:
        makedirs(args.output_dir, exist_ok=True)
    except OSError as error:
        print(error)
        return 127
    if not DURATIONS_RE.match(args.intervals):
        raise ValueError(
            args.intervals, "value is not valid. Must match", DURATIONS_RE.pattern
        )
    ecs_sd = EcsServiceDiscovery()
    ecs_sd.run(**vars(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

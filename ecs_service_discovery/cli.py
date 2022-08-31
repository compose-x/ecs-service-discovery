# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille <john@compose-x.io>

"""Console script for ecs_service_discovery."""
import argparse
import sys
from os import environ, makedirs

from boto3.session import Session

from ecs_service_discovery.ecs_service_discovery import ecs_service_discovery

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
        help="aws profile to use. Defaults to `default`",
        type=str,
        default="default",
    )
    parser.add_argument(
        "-p",
        "--prometheus-port",
        type=int,
        default=PROMETHEUS_METRICS_PORT,
        required=False,
        dest="prometheus_port",
    )
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    try:
        makedirs(args.output_dir, exist_ok=True)
    except OSError as error:
        print(error)
        return 127
    session = Session(profile_name=args.profile)
    ecs_service_discovery(
        args.output_dir, prometheus_metrics_port=args.prometheus_port, session=session
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

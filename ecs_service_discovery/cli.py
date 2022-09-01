# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille <john@compose-x.io>

"""Console script for ecs_service_discovery."""
import argparse
import sys
from datetime import datetime as dt
from os import environ, makedirs

from boto3.session import Session
from compose_x_common.compose_x_common import DURATIONS_RE, get_duration

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
    parser.add_argument("_", nargs="*")
    args = parser.parse_args()

    print("Arguments: " + str(args._))
    try:
        makedirs(args.output_dir, exist_ok=True)
    except OSError as error:
        print(error)
        return 127
    if args.profile:
        session = Session(profile_name=args.profile)
    else:
        session = Session()
    if not DURATIONS_RE.match(args.intervals):
        raise ValueError(
            args.intervals, "value is not valid. Must match", DURATIONS_RE.pattern
        )
    now = dt.now()
    interval_rtime = get_duration(args.intervals)
    intervals_in_seconds = round((now + interval_rtime - now).total_seconds())
    print("Scanning every", interval_rtime.normalized())
    ecs_service_discovery(
        args.output_dir,
        prometheus_metrics_port=args.prometheus_port,
        refresh_interval=intervals_in_seconds,
        session=session,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover

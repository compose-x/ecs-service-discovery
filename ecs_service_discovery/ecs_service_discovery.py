# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille <john@compose-x.io>

"""Main module."""

from __future__ import annotations

import logging
import signal
from datetime import datetime as dt
from time import sleep

from boto3.session import Session
from compose_x_common.aws.ecs import CLUSTER_NAME_FROM_ARN, list_all_ecs_clusters
from compose_x_common.compose_x_common import get_duration, keyisset, set_else_none
from prometheus_client import start_http_server

from ecs_service_discovery.ecs_sd_common import merge_tasks_and_hosts
from ecs_service_discovery.prometheus_sd import write_prometheus_targets_per_cluster
from ecs_service_discovery.stats import CLUSTER_PROMETHEUS_PROCESSING_TIME

LOG = logging.getLogger("ecs-sd")
LOG.setLevel(logging.DEBUG)


class EcsCluster:
    def __init__(self, arn: str):
        if not CLUSTER_NAME_FROM_ARN.match(arn):
            raise ValueError(
                f"Cluster ARN {arn} is invalid. Must match",
                CLUSTER_NAME_FROM_ARN.pattern,
            )
        self._arn = arn

    def __repr__(self):
        return f"{self.name} - {self.arn}"

    @property
    def arn(self) -> str:
        return self._arn

    @property
    def name(self) -> str:
        return CLUSTER_NAME_FROM_ARN.match(self._arn).group("name")


def define_intervals(**kwargs) -> int:
    if not keyisset("intervals", kwargs):
        return 30
    now = dt.now()
    interval_rtime = get_duration(kwargs["intervals"])
    intervals_in_seconds = round((now + interval_rtime - now).total_seconds())
    return intervals_in_seconds


def define_session(**kwargs) -> Session:
    profile = set_else_none("profile", kwargs)
    if profile:
        return Session(profile_name=profile)
    return Session()


class EcsServiceDiscovery:
    def __init__(self):
        self._run = True
        self._quit_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def run(self, output_dir: str, **kwargs: dict) -> int:
        """
        Main program loop. Will list the ECS Clusters with the associated IAM session.
        It will expose prometheus metrics, used for statistics on how well the discovery
        performs.
        """
        session = define_session(**kwargs)
        refresh_interval = define_intervals(**kwargs)
        prometheus_metrics_port = int(
            set_else_none("prometheus_metrics_port", kwargs, alt_value=8337)
        )
        _clusters: dict = {}
        start_http_server(prometheus_metrics_port)
        while self._run:
            try:
                for cluster_arn in list_all_ecs_clusters(session=session):
                    start = dt.now()
                    if cluster_arn not in _clusters:
                        _clusters[cluster_arn] = EcsCluster(cluster_arn)
                    cluster_targets = merge_tasks_and_hosts(
                        _clusters[cluster_arn], session
                    )
                    write_prometheus_targets_per_cluster(
                        _clusters[cluster_arn],
                        cluster_targets,
                        output_dir=output_dir,
                        **kwargs,
                    )
                    CLUSTER_PROMETHEUS_PROCESSING_TIME.labels(cluster_arn).set(
                        (dt.now() - start).total_seconds()
                    )
                for _wait in range(1, refresh_interval):
                    if not self._quit_now:
                        sleep(_wait)
            except KeyboardInterrupt:
                self._run = False
                self._quit_now = True
        return 0

    def exit_gracefully(self, signum, event):
        print(f"Signal {signum} received")
        self._run = False
        self._quit_now = True

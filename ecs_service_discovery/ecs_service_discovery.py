# SPDX-License-Identifier: MPL-2.0
# Copyright 2020-2022 John Mille <john@compose-x.io>

"""Main module."""

from __future__ import annotations

from datetime import datetime as dt
from time import sleep

from boto3.session import Session
from compose_x_common.aws import get_session
from compose_x_common.aws.ecs import CLUSTER_NAME_FROM_ARN, list_all_ecs_clusters
from prometheus_client import start_http_server

from ecs_service_discovery.ecs_sd_common import merge_tasks_and_hosts
from ecs_service_discovery.prometheus_sd import write_prometheus_targets_per_cluster
from ecs_service_discovery.stats import CLUSTER_PROMETHEUS_PROCESSING_TIME


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


def ecs_service_discovery(
    output_dir: str,
    prometheus_metrics_port: int = 8337,
    refresh_interval: int = 10,
    session: Session = None,
    **kwargs,
) -> int:
    """
    Main program loop. Will list the ECS Clusters with the associated IAM session.
    It will expose prometheus metrics, used for statistics on how well the discovery
    performs.
    """
    session = get_session(session)
    _continue_to_work: bool = True
    _clusters: dict = {}
    start_http_server(prometheus_metrics_port)
    while _continue_to_work:
        try:
            for cluster_arn in list_all_ecs_clusters(session=session):
                start = dt.now()
                if cluster_arn not in _clusters:
                    _clusters[cluster_arn] = EcsCluster(cluster_arn)
                cluster_targets = merge_tasks_and_hosts(_clusters[cluster_arn], session)
                write_prometheus_targets_per_cluster(
                    _clusters[cluster_arn], cluster_targets, output_dir
                )
                CLUSTER_PROMETHEUS_PROCESSING_TIME.labels(cluster_arn).set(
                    (dt.now() - start).total_seconds()
                )
            sleep(refresh_interval)
        except KeyboardInterrupt:
            _continue_to_work = False
    return 0

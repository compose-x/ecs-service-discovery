#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2022 John Mille <john@compose-x.io>

from __future__ import annotations

from prometheus_client import Gauge

CLUSTER_TASKS = Gauge(
    "cluster_tasks",
    "Number of tasks in the cluster",
    labelnames=["cluster_arn"],
)
CLUSTER_INSTANCES = Gauge(
    "cluster_instances",
    "Number of ECS Instances in the cluster",
    labelnames=["cluster_arn"],
)
CLUSTER_PROMETHEUS_PROCESSING_TIME = Gauge(
    "cluster_tasks_processing_time",
    "Amount of time spent scanning the cluster",
    labelnames=["cluster_arn"],
)
PROMETHEUS_TARGETS = Gauge(
    "ecs_sd_prometheus_targets",
    "Number of ECS discovered targets",
    labelnames=["cluster_arn"],
)

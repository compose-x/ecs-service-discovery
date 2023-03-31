#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2022 John Mille <john@compose-x.io>

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import yaml

try:
    from yaml import CDumper as Dumper
    from yaml import CSafeDumper as SafeDumper
except ImportError:
    from yaml import Dumper, SafeDumper

if TYPE_CHECKING:
    from ecs_service_discovery.ecs_service_discovery import EcsCluster

from compose_x_common.compose_x_common import keyisset, set_else_none

from ecs_service_discovery.ecs_sd_common import get_container_host_ip
from ecs_service_discovery.stats import PROMETHEUS_TARGETS


def group_targets_by_labels(targets: list[dict]) -> list[dict]:
    """
    Groups the targets together when there is identical labels match.
    """
    result_targets: list[dict] = [targets[0]]
    for target in targets[1:]:
        target_labels = target["labels"]
        for result_target in result_targets:
            if result_target["labels"] == target_labels:
                for _target_host in target["targets"]:
                    if _target_host not in result_target["targets"]:
                        result_target["targets"].append(_target_host)
                break
        else:
            result_targets.append(target)

    return result_targets


def identify_prometheus_enabled_targets(
    tasks: list[dict],
    prometheus_port_label: str = "ecs_sd_prometheus_container_port",
    prometheus_job_label: str = "ecs_sd_prometheus_job_name",
) -> list:
    """
    Goes over each task, checks if the prometheus labels are present for mapping.

    :param tasks: List of tasks in the cluster, enriched with the task definition
    :param prometheus_port_label: DockerLabel name to identify container port to probe for metrics
    :param prometheus_job_label: Dockerlabel name to identify container to monitor and job to associate with

    Returns the task and prometheus host mapping
    """
    prom_mapping: list = []
    for task in tasks:
        _task_def = task["_taskDefinition"]
        _host_ip = get_container_host_ip(task)
        for container in _task_def["containerDefinitions"]:
            labels = set_else_none("dockerLabels", container)
            if not labels or (
                prometheus_port_label not in labels
                or prometheus_job_label not in labels
            ):
                continue
            prometheus_port = int(labels[prometheus_port_label])
            definition = create_prometheus_target_definition(
                task,
                labels[prometheus_job_label],
                _host_ip,
                container,
                prometheus_port,
            )
            if definition:
                prom_mapping.append(definition)
    if not prom_mapping:
        return []
    return group_targets_by_labels(prom_mapping)


def write_prometheus_targets_per_cluster(
    cluster: EcsCluster, cluster_targets: list[dict], output_dir: str, **kwargs
) -> None:
    """
    Writes file for prometheus scraping. Generates prometheus stats metrics
    """
    cluster_prometheus_targets = identify_prometheus_enabled_targets(cluster_targets)
    PROMETHEUS_TARGETS.labels(cluster.arn).set(
        sum(len(_t["targets"]) for _t in cluster_prometheus_targets)
    )
    file_format = set_else_none("prometheus_output_format", kwargs, alt_value="json")
    file_path = f"{output_dir}/{cluster.name}.{file_format}"
    if file_format == "yaml":
        with open(file_path, "w") as targets_fd:
            targets_fd.write(yaml.dump(cluster_prometheus_targets, Dumper=SafeDumper))
    else:
        with open(file_path, "w") as targets_fd:
            targets_fd.write(
                json.dumps(cluster_prometheus_targets, separators=(",", ":"), indent=1)
            )


def set_labels(task: dict, container_name, job_name: str) -> dict:
    task_def = task["_taskDefinition"]
    for container_def in task_def["containerDefinitions"]:
        if container_name == container_def["name"]:
            break
    else:
        raise KeyError(
            f"Container definition for {container_name} not found in task definition",
            task_def["taskDefinitionArn"],
            [_container["name"] for _container in task_def["containerDefinitions"]],
        )
    labels = {
        "job": job_name,
        "ecs_cluster_arn": task["clusterArn"],
        "ecs_task_definition_arn": task_def["taskDefinitionArn"],
        "ecs_task_family": task_def["family"],
        "ecs_task_launch_type": task["launchType"],
    }
    labels.update(container_def["dockerLabels"])
    task_instance = set_else_none("_instance", task)
    if task_instance:
        labels["ecs_task_instance"]: str = task_instance["containerInstanceArn"]
        if keyisset("ec2InstanceId", task_instance):
            labels["ecs_instance_ec2_instance_id"] = task_instance["ec2InstanceId"]
    return labels


def create_prometheus_target_definition(
    task: dict, job_name: str, host_ip: str, container: dict, prometheus_port: int
) -> dict:
    """
    Maps container from task_definition to task, identifies the prometheus scan port, returns host target.

    :param task: The ECS Task running the containers
    :param job_name: The job_name to use for the target
    :param host_ip: The IP address of the host
    :param container: The container definition from the task definition
    :param prometheus_port: The port to probe for metrics

    Returns the target definition for the prometheus scraping.

    :raises KeyError: If the container definition is not found in the task definition.
    """
    container_name = container["name"]

    for task_container in task["containers"]:
        if container_name != task_container["name"]:
            continue
        network_bindings = set_else_none("networkBindings", task_container, [])
        port_mappings = set_else_none("portMappings", container, [])
        if network_bindings:
            for network_config in network_bindings:
                if int(network_config["containerPort"]) == int(prometheus_port):
                    scraping_port = int(
                        set_else_none(
                            "hostPort",
                            network_config,
                            alt_value=set_else_none("containerPort", network_config),
                        )
                    )
                    break
            else:
                print("No prometheus port found for task network settings")
                return {}
        elif not network_bindings and port_mappings:
            for network_config in port_mappings:
                if int(network_config["containerPort"]) == int(prometheus_port):
                    scraping_port = int(
                        set_else_none(
                            "hostPort",
                            network_config,
                            alt_value=set_else_none("containerPort", network_config),
                        )
                    )
                    break
            else:
                print("No prometheus port found for task network settings")
                return {}
        else:
            return {}

        labels = set_labels(task, task_container["name"], job_name)

        return {
            "labels": labels,
            "targets": [f"{host_ip}:{scraping_port}"],
        }

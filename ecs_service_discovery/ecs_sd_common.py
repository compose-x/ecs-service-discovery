#  SPDX-License-Identifier: MPL-2.0
#  Copyright 2020-2022 John Mille <john@compose-x.io>

"""
ECS Wrapper functions, producing an output re-usable for all targeted SD services.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs_service_discovery.ecs_service_discovery import EcsCluster

from boto3 import Session
from compose_x_common.aws import get_session
from compose_x_common.aws.ecs.instances import (
    describe_all_instances,
    list_all_instances,
)
from compose_x_common.aws.ecs.tasks import describe_all_tasks
from compose_x_common.compose_x_common import keyisset, set_else_none

from ecs_service_discovery.stats import CLUSTER_INSTANCES, CLUSTER_TASKS


def retrieve_hosts_ips(cluster: EcsCluster, session: Session = None) -> dict:
    session = get_session(session)
    active_cluster_instances = list_all_instances(
        cluster.arn, session=session, status="ACTIVE"
    )
    _cluster_instances = describe_all_instances(
        cluster.arn, active_cluster_instances, return_as_mapping=True
    )
    for _instance in _cluster_instances.values():
        if _instance["ec2InstanceId"].startswith("i-"):
            instance = session.resource("ec2").Instance(_instance["ec2InstanceId"])
            _instance["IPAddress"] = instance.private_ip_address
        elif _instance["ec2InstanceId"].startswith("mi-"):
            instance_r = session.client("ssm").describe_instance_information(
                InstanceInformationFilterList=[
                    {"key": "InstanceIds", "valueSet": [_instance["ec2InstanceId"]]}
                ]
            )
            _instance["IPAddress"] = instance_r["InstanceInformationList"][0][
                "IPAddress"
            ]
    return _cluster_instances


def enrich_task_information(
    tasks: list[dict], instances: dict, session: Session = None
) -> None:
    session = get_session(session)
    ecs_client = session.client("ecs")
    for task in tasks:
        task["_taskDefinition"] = ecs_client.describe_task_definition(
            taskDefinition=task["taskDefinitionArn"]
        )["taskDefinition"]
        task_instance_arn = set_else_none("containerInstanceArn", task)
        if not task_instance_arn:
            continue
        if task_instance_arn in instances:
            task["_instance"] = instances[task_instance_arn]


def get_container_host_ip(task: dict) -> str:
    """
    Function that will identify the IP address used by the task.
    """
    attachments = set_else_none("attachments", task, alt_value=[])
    eni_attachment = None
    for attachment in attachments:
        if attachment["type"] == "ElasticNetworkInterface":
            eni_attachment = attachment
            break
    if (
        keyisset("containerInstanceArn", task)
        and not eni_attachment
        and keyisset("_instance", task)
    ):
        return task["_instance"]["IPAddress"]
    elif eni_attachment:
        for detail in eni_attachment["details"]:
            if not isinstance(detail, dict):
                continue
            if keyisset("name", detail) and detail["name"] == "privateIPv4Address":
                return detail["value"]
        raise AttributeError(
            "Unable to get the IP address for ENI attachment", eni_attachment
        )


def merge_tasks_and_hosts(cluster: EcsCluster, session: Session = None) -> list:
    """
    Puts together the task, the task definition and if applicable, the ecs container instance.
    Can be used to map services out based on future requirements.
    """
    session = get_session(session)
    _cluster_instances = retrieve_hosts_ips(cluster, session=session)
    _cluster_tasks = describe_all_tasks(cluster.arn, session=session)
    enrich_task_information(_cluster_tasks, _cluster_instances, session=session)
    CLUSTER_TASKS.labels(cluster.arn).set(int(len(_cluster_tasks)))
    CLUSTER_INSTANCES.labels(cluster.arn).set(int(len(_cluster_instances.keys())))
    return _cluster_tasks

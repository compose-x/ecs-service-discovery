=====================
ECS Service Discovery
=====================

.. image:: https://img.shields.io/pypi/v/ecs_service_discovery.svg
        :target: https://pypi.python.org/pypi/ecs_service_discovery

Yet another tool to perform ECS API based service discovery.
Primarily aimed at gapping the lack of integrations for ECS Anywhere.

Features
==========

* Creates Prometheus scraping configuration, from scanning ECS clusters & services, based on docker labels

Installation
==============

Docker
--------

Head to `Public ECR`_ to obtain the image

.. code-block::

    docker run --rm -it -v ~/.aws:/root/.aws public.ecr.aws/compose-x/ecs-service-discovery


Python
---------

For your user only

.. code-block::

    pip install pip --user ecs-service-discovery

Via virtual environment

.. code-block::

    pip install ecs-service-discovery


Usage
=======

.. code-block::

    usage: ecs-sd [-h] [-d OUTPUT_DIR] [--profile PROFILE] [-p PROMETHEUS_PORT] [--intervals INTERVALS] [--prometheus-output-format PROMETHEUS_OUTPUT_FORMAT] [_ ...]

    positional arguments:
      _

    options:
      -h, --help            show this help message and exit
      -d OUTPUT_DIR, --output_dir OUTPUT_DIR
      --profile PROFILE     aws profile to use. Defaults to SDK default behaviour
      -p PROMETHEUS_PORT, --prometheus-port PROMETHEUS_PORT
      --intervals INTERVALS
                            Time between ECS discovery intervals
      --prometheus-output-format PROMETHEUS_OUTPUT_FORMAT
                            Change the format of generated files. JSON or YAML.

Examples
==========

ECS Compose-X
-----------------

Install `ecs-compose-x`_ & deploy to AWS

.. hint::

    you will need to use the `x-vpc`_ extension to deploy the service in the right VPC to get prometheus scraping.
    you can use the `x-cluster`_ extension to specify the ECS Cluster you want to deploy the service to.

Docker Compose
-----------------

After cloning the repository, run `docker compose up`. It will spin the service discovery, along with prometheus & grafana to run the demo with.
You can access prometheus via `localhost:9090` and grafana via `localhost:3000` (admin:admin by default).

In prometheus, you can look at the configuration and service discovery. You should see the discovered targets that prometheus is going to try
to scrape.

AWS Policy requirements
=========================

.. code-block:: yaml

          PolicyName: ECSServiceDiscoverySimple
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - ecs:ListClusters
                  - ecs:ListContainerInstances
                  - ecs:ListTasks
                  - ecs:DescribeContainerInstances
                  - ssm:DescribeInstanceInformation
                  - ecs:DescribeTasks
                  - ecs:DescribeTaskDefinition
                Resource: '*'


.. _Public ECR: https://gallery.ecr.aws/compose-x/ecs-service-discovery
.. _ecs-compose-x: https://docs.compose-x.io/installation.html
.. _x-cluster: https://docs.compose-x.io/syntax/compose_x/ecs_cluster.html
.. _x-vpc: https://docs.compose-x.io/syntax/compose_x/vpc.html

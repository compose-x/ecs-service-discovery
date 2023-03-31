=======
History
=======

0.1.0 (2023-03-31)
------------------

First release on PyPI.

Supports ECS Tasks discovery running on
* ECS with Fargate
* ECS with EC2 (requires ``awsvpc`` networking mode)
* ECS with ECS Anywhere (SSM managed instances)

Produces files for
* Prometheus service discovery (tasks grouped by labels)

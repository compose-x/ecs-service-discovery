ARG BUILD_IMAGE=public.ecr.aws/lambda/python:3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:alpine

FROM $BUILD_IMAGE as builder
WORKDIR /app
COPY ecs_service_discovery /app/ecs_service_discovery/
RUN ls -lRA /app/
COPY README.rst LICENSE pyproject.toml /app/
RUN pip install pip poetry -U
RUN poetry build

FROM $BASE_IMAGE
WORKDIR /app
COPY --from=builder /app/dist/*.whl /app
RUN pip install --no-cache-dir pip -U; pip install --no-cache-dir /app/*.whl
RUN ls -lA /usr/local/lib/python3.10/site-packages/ecs_service_discovery*
COPY run.sh /app/
RUN chmod +x run.sh
ENTRYPOINT ["/app/run.sh"]

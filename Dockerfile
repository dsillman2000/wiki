# Multi-stage build for wiki-client Docker image

FROM python:3.12-slim AS builder

RUN pip install uv

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./

ARG PACKAGE_VERSION=1.0.0
ENV UV_DYNAMIC_VERSIONING_BYPASS=$PACKAGE_VERSION

RUN uv pip install --system build hatchling uv-dynamic-versioning

COPY wiki_client ./wiki_client

RUN python -m build --wheel --no-isolation .

FROM python:3.12-slim

COPY --from=builder /build/dist/*.whl ./
RUN pip install --no-cache-dir ./*.whl && rm -f ./*.whl

RUN groupadd --gid 1000 wiki && \
    useradd --uid 1000 --gid wiki --shell /bin/bash --create-home wiki

USER wiki
WORKDIR /home/wiki

ENTRYPOINT ["wiki"]

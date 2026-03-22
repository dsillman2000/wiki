# Multi-stage build for wiki-client Docker image

FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /build
COPY pyproject.toml uv.lock README.md ./

ARG PACKAGE_VERSION=1.0.0
ENV PACKAGE_VERSION=$PACKAGE_VERSION

RUN uv pip install --system build hatchling uv-dynamic-versioning

COPY wiki_client ./wiki_client

RUN git init && \
    git config user.email "build@example.com" && \
    git config user.name "Build" && \
    git add -A && \
    git commit -m "temp"

RUN python -m build --wheel --no-isolation .

FROM python:3.12-slim

RUN pip install uv

COPY --from=builder /build/dist/*.whl ./
RUN uv pip install --system *.whl

RUN groupadd --gid 1000 wiki && \
    useradd --uid 1000 --gid wiki --shell /bin/bash --create-home wiki

USER wiki
WORKDIR /home/wiki

ENTRYPOINT ["wiki"]

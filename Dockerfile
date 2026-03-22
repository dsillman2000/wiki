# Multi-stage build for minimal wiki CLI Docker image
# Optimized for size and security using Debian slim base with statically downloaded binaries

# Stage 1: Download binaries
FROM alpine:3.19 AS binary-downloader

RUN apk add --no-cache \
    curl \
    tar \
    gzip \
    ca-certificates

WORKDIR /tmp/tools

# Download htmlq binary
RUN curl -fsSL https://github.com/mgdm/htmlq/releases/download/v0.4.0/htmlq-x86_64-linux.tar.gz | tar xz

# Download and extract glow binary
RUN curl -fsSL https://github.com/charmbracelet/glow/releases/download/v2.1.1/glow_2.1.1_Linux_x86_64.tar.gz | tar xz && \
    mv glow_2.1.1_Linux_x86_64/glow . && \
    rm -rf glow_2.1.1_Linux_x86_64

# Stage 2: Runtime environment - Debian slim for better compatibility and smaller footprint
FROM debian:12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    pandoc \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy binaries from downloader stage
COPY --from=binary-downloader /tmp/tools/htmlq /usr/local/bin/
COPY --from=binary-downloader /tmp/tools/glow /usr/local/bin/

RUN chmod +x /usr/local/bin/htmlq /usr/local/bin/glow

# Copy wiki script
COPY wiki /usr/local/bin/
RUN chmod +x /usr/local/bin/wiki

# Create non-root user for security best practices
RUN groupadd -g 1000 wiki && \
    useradd -m -u 1000 -g wiki wiki

USER wiki
WORKDIR /home/wiki

ENTRYPOINT ["wiki"]

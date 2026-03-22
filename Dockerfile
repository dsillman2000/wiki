# Multi-stage build for minimal wiki CLI Docker image
# Optimized for size and security using distroless base with compressed binaries

ARG TARGETARCH

# Stage 1: Download and compress binaries
FROM alpine:3.19 AS binary-downloader

RUN apk add --no-cache \
    curl \
    tar \
    gzip \
    ca-certificates \
    upx

WORKDIR /tmp/tools

# Download htmlq binary (supports amd64 and arm64)
RUN case "${TARGETARCH}" in \
        arm64) ARCH="aarch64" ;; \
        *) ARCH="x86_64" ;; \
    esac && \
    curl -fsSL "https://github.com/mgdm/htmlq/releases/download/v0.4.0/htmlq-${ARCH}-linux.tar.gz" | tar xz

# Download and compress glow binary
RUN case "${TARGETARCH}" in \
        arm64) ARCH="arm64" ;; \
        *) ARCH="x86_64" ;; \
    esac && \
    curl -fsSL "https://github.com/charmbracelet/glow/releases/download/v2.1.1/glow_2.1.1_Linux_${ARCH}.tar.gz" | tar xz && \
    mv glow_2.1.1_Linux_${ARCH}/glow . && \
    rm -rf glow_2.1.1_Linux_${ARCH}

# Download pandoc binary (smaller than apt package)
RUN case "${TARGETARCH}" in \
        arm64) ARCH="arm64" ;; \
        *) ARCH="amd64" ;; \
    esac && \
    curl -fsSL "https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-linux-${ARCH}.tar.gz" | tar xz && \
    mv pandoc-3.1.13/bin/pandoc . && \
    rm -rf pandoc-3.1.13

# Compress binaries with UPX
RUN upx --best /tmp/tools/htmlq /tmp/tools/glow /tmp/tools/pandoc

# Stage 2: Runtime environment - Distroless base for minimal size
FROM gcr.io/distroless/base-debian12

COPY --from=binary-downloader /tmp/tools/htmlq /usr/local/bin/
COPY --from=binary-downloader /tmp/tools/glow /usr/local/bin/
COPY --from=binary-downloader /tmp/tools/pandoc /usr/local/bin/

RUN chmod +x /usr/local/bin/htmlq /usr/local/bin/glow /usr/local/bin/pandoc

# Copy wiki script
COPY wiki /usr/local/bin/
RUN chmod +x /usr/local/bin/wiki

# Create non-root user for security best practices
RUN addgroup -g 1001 wiki && \
    adduser -D -u 1001 -G wiki wiki

USER wiki
WORKDIR /home/wiki

ENTRYPOINT ["wiki"]

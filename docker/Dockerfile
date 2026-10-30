# syntax=docker/dockerfile:1.7
# Heretek-Rigs fleet container image (targets: slim, full).
#
#   slim: rig + pi + $HERETEK_TOOLS (permission system, AST/LSP, 8 npm MCP
#         servers) + uvx-backed PyPI MCP servers. No browsers, no radare2.
#   full: slim + Playwright Chromium (+ CHROME_PATH for chrome-devtools-mcp)
#         + Debian radare2 + compiled radare2-mcp@1.9.0 (-R) binary.
#
# Fail-closed rules honored: non-root heretek (uid 1000), no compilers in the
# runtime layer, pinned Node/npm/uv versions, build-time verify + self-test,
# secrets NEVER baked in (staged at runtime by docker-entrypoint.sh).

ARG BASE_IMAGE=debian:bookworm-slim@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251
ARG NODE_VERSION=22.22.1
ARG UV_VERSION=0.13.3
ARG OPENRIG_VERSION=0.7.5
ARG PI_VERSION=1.4.0

# ---------------------------------------------------------------- builder ---
FROM ${BASE_IMAGE} AS builder
ARG TARGETARCH NODE_VERSION UV_VERSION OPENRIG_VERSION PI_VERSION
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl git g++ gcc libc6-dev make patch pkg-config python3 xz-utils; \
    rm -rf /var/lib/apt/lists/*; \
    case "${TARGETARCH}" in \
      amd64) NODE_ARCH="x64"; UV_ARCH="x86_64-unknown-linux-gnu" ;; \
      arm64) NODE_ARCH="arm64"; UV_ARCH="aarch64-unknown-linux-gnu" ;; \
      "") echo "error: TARGETARCH empty (enable BuildKit)" >&2; exit 1 ;; \
      *)  echo "error: unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    curl -fsSLo /tmp/node.tar.xz \
      "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${NODE_ARCH}.tar.xz"; \
    tar -xJf /tmp/node.tar.xz -C /usr/local --strip-components=1 --no-same-owner; \
    rm -f /tmp/node.tar.xz; \
    curl -fsSLo /tmp/uv.tar.gz \
      "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${UV_ARCH}.tar.gz"; \
    tar -xzf /tmp/uv.tar.gz -C /usr/local/bin --strip-components=1 --no-same-owner; \
    rm -f /tmp/uv.tar.gz; \
    node --version; npm --version; uv --version
RUN set -eux; \
    npm install -g "@openrig/cli@${OPENRIG_VERSION}" "@earendil-works/pi-coding-agent@${PI_VERSION}"; \
    node "$(npm root -g)/@openrig/cli/scripts/check-abi.mjs"; \
    rig --version; pi --version
# $HERETEK_TOOLS content, staged here so the runtime layer stays compiler-free.
ENV HERETEK_TOOLS=/opt/heretek/tools
RUN set -eux; \
    mkdir -p "${HERETEK_TOOLS}/pi-packages" "${HERETEK_TOOLS}/mcp" "${HERETEK_TOOLS}/bin" "${HERETEK_TOOLS}/src"; \
    npm --prefix "${HERETEK_TOOLS}/pi-packages" install --no-audit --no-fund \
      @gotgenes/pi-permission-system@41.0.0 \
      pi-lsp-extension@1.4.0 \
      pi-ast-grep@0.1.0; \
    npm --prefix "${HERETEK_TOOLS}/mcp" install --no-audit --no-fund \
      codebase-memory-mcp@0.12.1 \
      @upstash/context7-mcp@4.4.4 \
      @modelcontextprotocol/server-memory@2.0.0 \
      @playwright/mcp@0.0.83 \
      chrome-devtools-mcp@1.11.0 \
      @mobilenext/mobile-mcp@1.0.12 \
      mcp-openapi-schema-explorer@1.3.5 \
      kubernetes-mcp-server@0.0.67; \
    npm cache clean --force
# radare2-mcp binary (full target only copies the artifact out of here).
ARG INSTALL_R2MCP=false
RUN set -eux; \
    if [ "${INSTALL_R2MCP}" = "true" ]; then \
      # NOTE: r2mcp 1.9.0 tracks radare2 6.2.4 per its own CI (R2V env); 5.9.8
      # headers lack the uint8_t r_base64 API it calls. The devsec sidecar
      # (radareorg/radare2:5.9.8) is a separate interactive service.
      git clone --depth 1 --branch 6.2.4 https://github.com/radare/radare2 "${HERETEK_TOOLS}/src/radare2"; \
      (cd "${HERETEK_TOOLS}/src/radare2" && ./configure --prefix=/usr/local >/dev/null && make -j"$(nproc)" >/dev/null && make install >/dev/null && ldconfig); \
      rm -rf "${HERETEK_TOOLS}/src/radare2"; \
      r2 -v; \
      git clone --depth 1 --branch 1.9.0 https://github.com/radareorg/radare2-mcp "${HERETEK_TOOLS}/src/radare2-mcp"; \
      (cd "${HERETEK_TOOLS}/src/radare2-mcp" && ./configure >/dev/null && make >/dev/null); \
      install -m 0755 "${HERETEK_TOOLS}/src/radare2-mcp/src/r2mcp" "${HERETEK_TOOLS}/bin/r2mcp"; \
      rm -rf "${HERETEK_TOOLS}/src/radare2-mcp"; \
    fi

# -------------------------------------------------------------------- slim ---
FROM ${BASE_IMAGE} AS slim
ARG NODE_VERSION
ENV HERETEK_HOME=/opt/heretek/heretek-rigs \
    HERETEK_TOOLS=/opt/heretek/tools \
    HERETEK_SECRETS=/home/heretek/.config/heretek-rigs/secrets \
    OPENRIG_HOME=/home/heretek/.openrig \
    HERETEK_WORKSPACE=/workspace \
    TERM=xterm-256color \
    PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin
RUN set -eux; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      bubblewrap ca-certificates curl git jq make procps python3 python3-pip \
      python3-venv ripgrep tini tmux xz-utils; \
    rm -rf /var/lib/apt/lists/*; \
    pip install --no-cache-dir --break-system-packages pyyaml jsonschema
COPY --from=builder /usr/local /usr/local
COPY --from=builder /opt/heretek/tools /opt/heretek/tools
RUN set -eux; \
    node --version; npm --version; uv --version; \
    rig --version; pi --version; bwrap --version; \
    test -d /opt/heretek/tools/pi-packages/node_modules/@gotgenes/pi-permission-system
RUN set -eux; \
    groupadd --gid 1000 heretek; \
    useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash heretek; \
    mkdir -p /opt/heretek/heretek-rigs /home/heretek/.openrig /workspace /run/heretek-secrets; \
    mkdir -p -m 0700 /home/heretek/.config/heretek-rigs/secrets; \
    chown -R heretek:heretek /opt/heretek /home/heretek /workspace /run/heretek-secrets
USER heretek
WORKDIR /opt/heretek/heretek-rigs
COPY --chown=heretek:heretek . /opt/heretek/heretek-rigs/
RUN set -eux; \
    git config --global --add safe.directory /opt/heretek/heretek-rigs; \
    chmod +x scripts/*.sh scripts/*.py; \
    bash ./scripts/verify-rigs.sh --check-only; \
    python3 ./scripts/audit_loop.py --self-test
COPY docker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
USER root
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh
USER heretek
WORKDIR /opt/heretek/heretek-rigs
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD rig daemon status >/dev/null 2>&1 || exit 1
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]

# -------------------------------------------------------------------- full ---
FROM slim AS full
USER root
RUN ldconfig
# Debian radare2 (r2mcp shells out to r2/rabin2) + Playwright Chromium for the
# browser MCP servers. Chromium follows the Playwright revision bundled with
# the pinned @playwright/mcp installation.
RUN set -eux; \
    r2 -v
COPY --from=builder --chown=heretek:heretek /opt/heretek/tools/bin/r2mcp /opt/heretek/tools/bin/r2mcp
RUN set -eux; \
    PLAYWRIGHT_CLI="$(node -p "require('path').dirname(require.resolve('playwright/package.json', { paths: ['${HERETEK_TOOLS}/mcp/node_modules/@playwright/mcp'] }))")/cli.js"; \
    node "${PLAYWRIGHT_CLI}" install-deps chromium; \
    rm -rf /var/lib/apt/lists/*
USER heretek
# Stable symlink: chrome-launcher honors $CHROME_PATH (must be the binary itself).
RUN set -eux; \
    PLAYWRIGHT_CLI="$(node -p "require('path').dirname(require.resolve('playwright/package.json', { paths: ['${HERETEK_TOOLS}/mcp/node_modules/@playwright/mcp'] }))")/cli.js"; \
    node "${PLAYWRIGHT_CLI}" install chromium; \
    CHROME_BIN="$(echo "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome | head -n 1)"; \
    test -x "${CHROME_BIN}"; \
    ln -sfn "${CHROME_BIN}" "$HOME/.cache/ms-playwright/chromium-chrome"; \
    test -x "$HOME/.cache/ms-playwright/chromium-chrome"
ENV CHROME_PATH=/home/heretek/.cache/ms-playwright/chromium-chrome
RUN set -eux; \
    test -x /opt/heretek/tools/bin/r2mcp; \
    /opt/heretek/tools/bin/r2mcp -h >/dev/null 2>&1 || true; \
    test -x "${CHROME_PATH}"
USER heretek
WORKDIR /opt/heretek/heretek-rigs
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/docker-entrypoint.sh"]
CMD ["bash"]

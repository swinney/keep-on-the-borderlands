# Containerfile — Keep on the Borderlands Ralph Loop sandbox.
#
# Built and run on a Linux host with rootless Podman.
# See docs/decisions/0001-container-runtime.md for the runtime choice and
# CLAUDE.md §6 for the broader container architecture.

FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    LANG=C.UTF-8

# System tools.
#   git              repo operations from inside the loop
#   curl, ca-certs   ad-hoc fetches, TLS
#   tmux             the loop is normally driven from host tmux, but having
#                    it inside is occasionally useful for stuck sessions
#   build-essential  for any Python wheel that needs to compile
#   nodejs, npm      required to install Claude Code via npm
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        curl \
        ca-certificates \
        tmux \
        build-essential \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

# Claude Code. Installed globally so the `claude` binary is on PATH for any
# user. The Ralph Loop invokes this with --dangerously-skip-permissions; the
# container boundary is what makes that acceptable.
RUN npm install -g @anthropic-ai/claude-code

# Python toolchain. Evennia pulls Django plus many transitive deps; pinning
# the leaves keeps image rebuilds reproducible without locking the whole
# transitive graph. evennia is pinned to match pyproject [project.dependencies]
# so the container's gates match the host's.
RUN pip install --no-cache-dir \
        evennia==6.0.0 \
        "scipy>=1.11,<2" \
        pytest \
        pytest-django \
        pytest-cov \
        mypy==2.1.0 \
        ruff==0.15.15 \
        pre-commit

# Non-root user. With rootless Podman the in-container UID is remapped
# through subuid back to the invoking host user, so files written under
# /workspace come out owned by you on the host filesystem. Match the host
# UID/GID at build time (override with --build-arg if yours differs).
ARG USER_UID=1000
ARG USER_GID=1000
RUN groupadd -g ${USER_GID} claude \
    && useradd -m -u ${USER_UID} -g ${USER_GID} -s /bin/bash claude

USER claude
WORKDIR /workspace
CMD ["bash"]

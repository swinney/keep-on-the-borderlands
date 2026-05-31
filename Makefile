# Convenience targets for the Ralph Loop container.
# See CLAUDE.md §6, docs/decisions/0001-container-runtime.md, and
# docs/decisions/0002-claude-auth.md.

IMAGE      := kotb-ralph
WORKSPACE  := $(CURDIR)
CLAUDE_DIR := $(WORKSPACE)/.ralph/claude-home

# Common podman flags for every run target.
#   --userns=keep-id  maps host UID/GID to the same IDs inside the container,
#                     so files written by the in-container `claude` user are
#                     owned by you on the host (bind mounts Just Work).
#   -v claude-home    persists Claude Code's auth across runs.
#   -v workspace      the project tree.
RUN_FLAGS := \
  --userns=keep-id \
  -v $(WORKSPACE):/workspace \
  -v $(CLAUDE_DIR):/home/claude/.claude

.PHONY: help build login loop loop-once shell clean

help:
	@echo "Targets:"
	@echo "  build      build the kotb-ralph container image"
	@echo "  login      one-time: run 'claude login' to authenticate via Pro/Max"
	@echo "  loop       start the Ralph Loop in the foreground (Ctrl-C to stop)"
	@echo "  loop-once  run one Claude Code turn against PROMPT.md (no loop)"
	@echo "  shell      drop into an interactive shell in the container"
	@echo "  clean      remove the container image (preserves saved auth)"

build:
	podman build \
	  --build-arg USER_UID=$$(id -u) \
	  --build-arg USER_GID=$$(id -g) \
	  -t $(IMAGE) -f Containerfile .

login:
	@mkdir -p $(CLAUDE_DIR)
	podman run --rm -it \
	  $(RUN_FLAGS) \
	  --name kotb-ralph-login \
	  $(IMAGE) \
	  claude login

loop:
	@mkdir -p $(CLAUDE_DIR)
	podman run --rm -it \
	  $(RUN_FLAGS) \
	  --name kotb-ralph-loop \
	  $(IMAGE) \
	  ./scripts/ralph.sh

loop-once:
	@mkdir -p $(CLAUDE_DIR)
	podman run --rm -it \
	  $(RUN_FLAGS) \
	  --name kotb-ralph-once \
	  $(IMAGE) \
	  bash -c 'claude -p --dangerously-skip-permissions < PROMPT.md'

shell:
	@mkdir -p $(CLAUDE_DIR)
	podman run --rm -it \
	  $(RUN_FLAGS) \
	  --name kotb-ralph-shell \
	  $(IMAGE)

clean:
	podman rmi $(IMAGE) || true

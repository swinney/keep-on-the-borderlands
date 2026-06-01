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
#   -e RALPH_MODEL    forwards the host RALPH_MODEL (if set) so the loop can run
#                     on a chosen model, e.g. RALPH_MODEL=claude-sonnet-4-6 make loop
RUN_FLAGS := \
  --userns=keep-id \
  -e RALPH_MODEL \
  -v $(WORKSPACE):/workspace \
  -v $(CLAUDE_DIR):/home/claude/.claude

.PHONY: help build login loop loop-once shell clean status fanout fanout-dry fanout-status fanout-land

help:
	@echo "Targets:"
	@echo "  build          build the kotb-ralph container image"
	@echo "  login          one-time: run 'claude login' to authenticate via Pro/Max"
	@echo "  loop           start the Ralph Loop in the foreground (Ctrl-C to stop)"
	@echo "  loop-once      run one Claude Code turn against PROMPT.md (no loop)"
	@echo "  status         print a digest of loop status (current turn, recent turns, STATUS)"
	@echo "  shell          drop into an interactive shell in the container"
	@echo "  clean          remove the container image (preserves saved auth)"
	@echo "  fanout         launch M10 tribe fan-out (clone/branch/pool, default concurrency 2)"
	@echo "  fanout-dry     dry-run: print the fanout plan (clones, branches, tasks, launch cmds)"
	@echo "  fanout-status  aggregate status digest across all active tribe clones"
	@echo "  fanout-land    merge clean tribe PRs (CI green + no Copilot inline comments)"

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
	  ./scripts/ralph.sh --once

shell:
	@mkdir -p $(CLAUDE_DIR)
	podman run --rm -it \
	  $(RUN_FLAGS) \
	  --name kotb-ralph-shell \
	  $(IMAGE)

status:
	@./scripts/ralph-status.sh

fanout:
	./scripts/fanout.sh

fanout-dry:
	./scripts/fanout.sh --dry-run

fanout-status:
	@./scripts/fanout-status.sh

fanout-land:
	./scripts/fanout-land.sh

clean:
	podman rmi $(IMAGE) || true

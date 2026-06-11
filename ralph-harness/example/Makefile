# Worked example: Makefile for the "Acme Widgets" sample. IMAGE/RUNTIME match
# example/ralph.conf (acme-loop / podman). Only those two values differ from
# ../templates/Makefile.template.

IMAGE      ?= acme-loop
RUNTIME    ?= podman
WORKSPACE  := $(CURDIR)
CLAUDE_DIR := $(WORKSPACE)/.ralph/claude-home
SCRIPTS    := ralph-harness/scripts

RUN_FLAGS := \
  --userns=keep-id \
  -e RALPH_MODEL \
  -v $(WORKSPACE):/workspace \
  -v $(CLAUDE_DIR):/home/claude/.claude

.PHONY: help build login loop loop-once shell status clean

help:
	@echo "Targets:"
	@echo "  build      build the $(IMAGE) sandbox image"
	@echo "  login      one-time: authenticate Claude Code (Pro/Max or API key)"
	@echo "  loop       run the Ralph Loop in the foreground (Ctrl-C to stop)"
	@echo "  loop-once  run exactly one turn against PROMPT.md (no loop)"
	@echo "  status     print a digest of loop status (host-side)"
	@echo "  shell      drop into an interactive shell in the container"
	@echo "  clean      remove the image (preserves saved auth)"

build:
	$(RUNTIME) build \
	  --build-arg USER_UID=$$(id -u) \
	  --build-arg USER_GID=$$(id -g) \
	  -t $(IMAGE) -f Containerfile .

login:
	@mkdir -p $(CLAUDE_DIR)
	$(RUNTIME) run --rm -it $(RUN_FLAGS) --name $(IMAGE)-login $(IMAGE) claude login

loop:
	@mkdir -p $(CLAUDE_DIR)
	$(RUNTIME) run --rm -it $(RUN_FLAGS) --name $(IMAGE) $(IMAGE) ./$(SCRIPTS)/ralph.sh

loop-once:
	@mkdir -p $(CLAUDE_DIR)
	$(RUNTIME) run --rm -it $(RUN_FLAGS) --name $(IMAGE)-once $(IMAGE) ./$(SCRIPTS)/ralph.sh --once

shell:
	@mkdir -p $(CLAUDE_DIR)
	$(RUNTIME) run --rm -it $(RUN_FLAGS) --name $(IMAGE)-shell $(IMAGE)

status:
	@./$(SCRIPTS)/ralph-status.sh

clean:
	$(RUNTIME) rmi $(IMAGE) || true

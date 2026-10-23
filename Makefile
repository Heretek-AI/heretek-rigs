# Heretek-Rigs Operations & Verification Makefile
#
# Target Framework: OpenRig v0.6.13 (CLI binary: `rig`)
# Primary Harness:  Pi Coding Agent v1.3.0 (`pi --mode rpc --no-approve`)
# Enforcement:      @gotgenes/pi-permission-system@41.0.0 ("*..*": "deny" guard)
# Primary Model:    opencode-go/muse-spark-1.3-contributor:high (OpenCode Go)

-include .env
export

COMPOSE := docker compose
SIDECAR_PROFILES ?=
RIG_BIN := $(shell command -v rig 2>/dev/null || true)

.DEFAULT_GOAL := help
.PHONY: help generate idempotent verify live-health test bootstrap-seats seed gate guard-profiles sidecars-up sidecars-down bundle-check audit-loop audit-sessions topology manifest-closure policy-verifier reconcile generate-tracker

help: ## List all documented Heretek-Rigs targets.
	@echo "Heretek-Rigs — 51-Agent OpenRig + Pi + OpenCode Go Fleet"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## ' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

generate: ## Deterministically generate all 51 AgentSpecs, 8 RigBundles, Roster, and Registry views from fleet/fleet.yaml.
	python3 ./scripts/generate-rigs.py

idempotent: ## Regenerate twice and fail if any byte differs (HR-8.1 determinism gate for CI/audits).
	python3 ./scripts/generate-rigs.py --check-idempotent

verify: ## Run the self-testing verification gate (schemas, digests, 51-role parity, DAGs, sidecars, unit tests).
	bash ./scripts/verify-rigs.sh
	python3 ./scripts/live-health.py

live-health: ## Warn-first live-fleet health gate (read-only; advisory exit 0, --strict to fail).
	python3 ./scripts/live-health.py

test: ## Run unit tests for seat rendering and permission configuration.
	python3 -m unittest tests/test_render_seat.py tests/test_sweep_typed_blocks.py tests/test_regen_gate.py tests/test_queue_id_discipline.py tests/test_queue_json_discipline.py tests/test_reconcile.py tests/test_generate_trackers.py -v

bootstrap-seats: ## Provision $OPENRIG_HOME/state/pi/<seat>/agent/ across all rigs.
	bash ./scripts/bootstrap-pi-seats.sh --all

seed: ## Seed one rig before launch: make seed RIG=defensive-sec-and-red-team
	python3 ./scripts/seed-rig.py rigs/$(RIG)/rig.yaml --allow-missing-secrets

gate: ## Gate-test one role against mock OpenAI + pi-permission-system: make gate ROLE=appsec-engineer
	bash ./scripts/gate-role.sh $(ROLE)

audit-sessions: ## Detect misattributed denials + false delivery claims: make audit-sessions [WORKSPACE=/path/to/seat-workspace]
	python3 ./scripts/audit_sessions.py $(if $(WORKSPACE),--workspace $(WORKSPACE))

topology: ## Render fleet wiring (graph.json, SVGs, matrix) + fail-closed referential gates: make topology OUT=/tmp/topo
	python3 ./scripts/topology.py --out $(or $(OUT),/tmp/heretek-topology)

guard-profiles: ## Fail-closed guard: refuse co-scheduling --profile mobile with devsec or web-research.
	@norm="$$(printf '%s' "$(SIDECAR_PROFILES)" | tr '\t\r\n\v\f,' '      ')"; \
	case " $$norm " in \
	  *" mobile "* ) \
	    case " $$norm " in \
	      *" devsec "*|*" web-research "* ) \
	        echo "error: refusing to co-schedule --profile mobile with devsec/web-research (privileged /dev/kvm emulator must stay isolated)" >&2; \
	        exit 1;; \
	    esac;; \
	esac

sidecars-up: guard-profiles ## Start sidecars: make sidecars-up SIDECAR_PROFILES="web-research"
	$(COMPOSE) -f docker-compose.sidecars.yml $(foreach p,$(SIDECAR_PROFILES),--profile $(p)) up -d

sidecars-down: ## Stop sidecar containers while preserving named volumes.
	$(COMPOSE) -f docker-compose.sidecars.yml down

bundle-check: verify ## Run `rig bundle check` across all 8 rigs when the OpenRig CLI (`rig`) is installed.
	@if [ -n "$(RIG_BIN)" ]; then \
		for r in rigs/*/; do \
			echo "Checking $$r with $(RIG_BIN) bundle check..."; \
			"$(RIG_BIN)" bundle check "$$r" --json; \
		done; \
	else \
		echo "Note: 'rig' CLI binary not on PATH; offline bundle-check rules already verified via ./scripts/verify-rigs.sh."; \
	fi

audit-loop: ## Run the automated OpenCode adversarial audit & remediation loop until 3 consecutive STATUS: NO_FINDINGS passes.
	python3 ./scripts/audit_loop.py

manifest-closure: ## Run the stage-time manifest-closure lint over staged manifests (issue #40).
	python3 ./scripts/manifest-closure.py --staged

policy-verifier: ## Run the stage-time policy-text verifier over staged policy files (issue #41).
	python3 ./scripts/policy-verifier.py --staged

reconcile: ## Diff dispatch tracker(s) against live queue state (read-only, TPM approval): make reconcile TRACKER=path/to/tracker.md [OUT=file].
	python3 ./scripts/reconcile.py --live --tracker $(TRACKER) $(if $(OUT),--out $(OUT))

generate-tracker: ## Emit a dispatch-tracker proposal from live queue state (read-only, TPM approval): make generate-tracker TRACKER=path/to/tracker.md OUT=file.
	python3 ./scripts/generate_trackers.py --live --tracker $(TRACKER) $(if $(OUT),--out $(OUT))

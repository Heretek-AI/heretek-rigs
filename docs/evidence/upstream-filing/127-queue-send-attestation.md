<!-- DRAFT ONLY — NOT FILED. Filing requires a separate explicit per-issue approval. -->
<!-- Post at: https://github.com/mvschwarz/openrig/issues/new (suggested template: feature_request.yml) -->
<!-- Our tracker: https://github.com/Heretek-AI/heretek-rigs/issues/127 -->

# [Draft] Queue/send operations need daemon-issued caller attestation

## Problem

Queue operations (`rig queue create`, and by extension send-path queue rows)
accept their sender identity as an unauthenticated claim. A forged
`--source` value, or a forged `OPENRIG_SESSION_NAME` environment claim, is
recorded by the daemon as the row's `sourceSession` with no challenge, no
grant check, and no seat process required. Any local caller can author a
queue row that a destination seat reads as sent by a different seat — including
a seat on a different rig.

## What we proved (repo-side, isolated scratch daemons, FOR-TEST-ONLY rows)

1. **Forged `--source` accepted pre-fix.** A peer sender value and a fully
   alien cross-rig sender value were both recorded verbatim as
   `sourceSession` on pending rows owned by another seat; neither create
   required attestation, a grant, or a running seat process. Verdict lines
   and receipt fields: `docs/evidence/09-send-identity-spoof.md:18-19`,
   `:22-25` (ids redacted; long-token grep over the file prints nothing).
2. **Bare environment claim serves any seat string.** Setting the session
   environment variable to an arbitrary seat name and calling the queue
   identity probe succeeds with exit 0 — the daemon serves any seat string
   with zero challenge (`docs/evidence/107-identity-m0.md`, section 7, via
   our issue `#127` linked above).
3. **No repo-side boundary is possible.** A same-rig cross-seat test showed a
   seat's own credential always resolves to itself, so impersonation through
   our layer is impossible — and symmetrically, there is no repo-side point
   where a forged daemon-level claim can be intercepted. Decision recorded:
   no queue-identity code built (fail-closed). Refutation write-up:
   `docs/reports/107-identity-rework3.md`; queue probe evidence:
   `docs/evidence/107-identity-queue.md`.

## What our repo-side mitigation does and does not do

We mint per-seat sender bindings (`rig mcp token add <name> --seat
<session> --rig <managed-rig>`, always scoped to seat AND rig) and verify
sender claims against them at our layer, with a revoke-and-replace rotation
runbook (revocation effective on the next request, no daemon restart:
`docs/evidence/09-send-identity-rotation.md:6-11`, `:36-37`).

**Attribution, not authentication:** these bindings let our tooling attribute
a sender claim to a grant we issued. They do not stop the daemon itself from
recording an unauthenticated claim — the daemon path this issue is about
remains open underneath them. Only a daemon-side change closes it.

## Ask

Daemon-issued caller attestation for queue operations (or equivalent): `rig
queue create/show/claim` should carry a verifiable caller identity derived
from the daemon's own session/process knowledge rather than the spoofable
environment claim, so a destination seat can distinguish a genuine sender
from a forged `sourceSession`. Happy to test against scratch daemons and
report back.

## Environment observed

- `rig 0.7.5`, loopback daemon, Linux. Repo-side proofs above were captured
  on isolated scratch environments with dummy credentials only.

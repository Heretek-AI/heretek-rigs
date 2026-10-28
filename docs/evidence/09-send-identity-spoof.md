# S0 spoof proof transcript (09-send-identity, Refs #9)

Pre-fix evidence: a forged `--source` sender is ACCEPTED on the unpatched
tree — the daemon records the claim with no attestation required, so the
destination seat would read the row as sent by the forged session.

- Scratch ONLY: loopback daemon under `/tmp/s0-09-send-identity/home`
  (`OPENRIG_HOME` isolated; live `~/.openrig` untouched), dummy keys only,
  repo bundle materialized read-only (`rig import --materialize-only`, no
  seat processes launched). Daemon stopped after the run.
- Spike: `/tmp/s0-spoof-proof.sh` (scratch-only, never committed).
- Redactions: qitem hex tails and daemon host ids replaced with
  `<...-redacted>` placeholders. Forged-sender identity lines are verbatim.
  `grep -rE '[A-Za-z0-9_-]{40,}'` over this file prints nothing.

## Verdict lines (verbatim)

accepted forged sender: red-ai-red-teamer@defensive-sec-and-red-team
SPOOF-OK pre-fix: forged sender red-ai-red-teamer@defensive-sec-and-red-team accepted (claim recorded, no attestation required)

Key receipt fields (verbatim, ids redacted): the forged peer claim lands as
`"sourceSession":"red-ai-red-teamer@defensive-sec-and-red-team"` with
`"state":"pending"` on a row owned by
`"destinationSession":"blue-appsec-engineer@defensive-sec-and-red-team"`;
the fully alien claim lands as `"sourceSession":"red-actor@other-rig"`.
Neither create required any attestation, grant, or seat process.

## Full transcript (redacted as above)

```
S0: starting isolated loopback daemon (OPENRIG_HOME=/tmp/s0-09-send-identity/home)
S0: daemon start rc=0 (see /tmp/s0-09-daemon-start.log)
--- topology: materialize repo bundle read-only (no seat processes) ---
Rig materialized: defensive-sec-and-red-team (01M617CEGW59NVR3TJMY25A363)
  blue.threat-modeler: materialized
  blue.appsec-engineer: materialized
  blue.cloud-sec-auditor: materialized
  blue.compliance-auditor: materialized
  red.ai-red-teamer: materialized
  red.binary-reverse-eng: materialized
  red.firmware-sec-analyst: materialized
--- probe A: OPENRIG_SESSION_NAME env sender claim ---
{
  "error": "Session or node 'blue-appsec-engineer@defensive-sec-and-red-team' not found in any managed rig. Check available sessions with: rig ps --nodes",
  "hint": "Reached daemon \"host-<redacted>\" at \"http://127.0.0.1:7433/\". Seat routing may point to a different OpenRig install. Compare OPENRIG_URL and OPENRIG_HOME in this shell with the daemon that launched this seat."
}
--- probe B1: forged PEER --source on queue create ---
Queue create request ID: qitem-20261028122229-<hex-redacted> (not proof of persistence). At the same endpoint and OPENRIG_HOME, run: rig queue show 'qitem-20261028122229-<hex-redacted>' --full --json. If retrying, repeat the same create with --id 'qitem-20261028122229-<hex-redacted>' and unchanged source, destination, body and options. A missing row does not rule out a pending commit; retrying without this ID creates new work.
{"pickup":{"state":"unclaimed"},"waiting":{"obligation":"qitem-20261028122229-<hex-redacted>","owner":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","actionableSince":"2026-10-28T12:22:29.056Z","blocker":null,"lastMeaningfulChange":{"id":1,"at":"2026-10-28T12:22:29.057Z"},"liveness":{"subject":"blue-appsec-engineer@defensive-sec-and-red-team","activity":"unknown","needsInput":{"count":0,"reason":null},"confidence":"unknown"},"nextBackstop":{"owner":"blue-appsec-engineer@defensive-sec-and-red-team","mechanism":"queue-stuck-sweep:unclaimed","dueAt":"2026-10-28T13:22:29.056Z","intervalSeconds":300},"deadlineAt":null},"qitemId":"qitem-20261028122229-<hex-redacted>","tsCreated":"2026-10-28T12:22:29.056Z","tsUpdated":"2026-10-28T12:22:29.056Z","sourceSession":"red-ai-red-teamer@defensive-sec-and-red-team","destinationSession":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","priority":"routine","tier":null,"tags":null,"blockedOn":null,"handedOffTo":null,"handedOffFrom":null,"expiresAt":null,"chainOfRecord":null,"body":"S0 spoof probe body FOR-TEST-ONLY","summary":"S0 spoof probe FOR-TEST-ONLY","evidenceRef":null,"humanIntent":null,"humanDetail":null,"replyTo":null,"humanQuestions":null,"humanAnswers":null,"delegatedDecision":null,"closureReason":null,"closureTarget":null,"closureRequiredAt":null,"claimedAt":null,"lastNudgeAttempt":null,"lastNudgeResult":null,"lastNudgeWireResult":null,"lastHeartbeat":null,"resolution":null,"targetRepo":null,"deliveryOutcome":null}
S0: qitemId=qitem-20261028122229-<hex-redacted>
{"pickup":{"state":"unclaimed"},"waiting":{"obligation":"qitem-20261028122229-<hex-redacted>","owner":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","actionableSince":"2026-10-28T12:22:29.056Z","blocker":null,"lastMeaningfulChange":{"id":1,"at":"2026-10-28T12:22:29.057Z"},"liveness":{"subject":"blue-appsec-engineer@defensive-sec-and-red-team","activity":"unknown","needsInput":{"count":0,"reason":null},"confidence":"unknown"},"nextBackstop":{"owner":"blue-appsec-engineer@defensive-sec-and-red-team","mechanism":"queue-stuck-sweep:unclaimed","dueAt":"2026-10-28T13:22:29.056Z","intervalSeconds":300},"deadlineAt":null},"qitemId":"qitem-20261028122229-<hex-redacted>","tsCreated":"2026-10-28T12:22:29.056Z","tsUpdated":"2026-10-28T12:22:29.056Z","sourceSession":"red-ai-red-teamer@defensive-sec-and-red-team","destinationSession":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","priority":"routine","tier":null,"tags":null,"blockedOn":null,"handedOffTo":null,"handedOffFrom":null,"expiresAt":null,"chainOfRecord":null,"body":"S0 spoof probe body FOR-TEST-ONLY","summary":"S0 spoof probe FOR-TEST-ONLY","evidenceRef":null,"humanIntent":null,"humanDetail":null,"replyTo":null,"humanQuestions":null,"humanAnswers":null,"delegatedDecision":null,"closureReason":null,"closureTarget":null,"closureRequiredAt":null,"claimedAt":null,"lastNudgeAttempt":"2026-10-28T12:22:29.077Z","lastNudgeResult":"unroutable: 'blue-appsec-engineer@defensive-sec-and-red-team' has no terminal transport on this daemon and names no registered human — no transport can hold this address (checked: tmux bindings + the human registry). Fix the address, or register the human with `rig gateway human add`.","lastNudgeWireResult":"unroutable: 'blue-appsec-engineer@defensive-sec-and-red-team' has no terminal transport on this daemon and names no registered human — no transport can hold this address (checked: tmux bindings + the human registry). Fix the address, or register the human with `rig gateway human add`.","lastHeartbeat":null,"resolution":null,"targetRepo":null,"deliveryOutcome":null,"destinationClass":"unroutable","ownerNotificationLevel":null}

--- probe B2: forged ALIEN --source on queue create ---
Queue create request ID: qitem-20261028122229-<hex-redacted> (not proof of persistence). At the same endpoint and OPENRIG_HOME, run: rig queue show 'qitem-20261028122229-<hex-redacted>' --full --json. If retrying, repeat the same create with --id 'qitem-20261028122229-<hex-redacted>' and unchanged source, destination, body and options. A missing row does not rule out a pending commit; retrying without this ID creates new work.
{"pickup":{"state":"unclaimed"},"waiting":{"obligation":"qitem-20261028122229-<hex-redacted>","owner":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","actionableSince":"2026-10-28T12:22:29.471Z","blocker":null,"lastMeaningfulChange":{"id":2,"at":"2026-10-28T12:22:29.472Z"},"liveness":{"subject":"blue-appsec-engineer@defensive-sec-and-red-team","activity":"unknown","needsInput":{"count":0,"reason":null},"confidence":"unknown"},"nextBackstop":{"owner":"blue-appsec-engineer@defensive-sec-and-red-team","mechanism":"queue-stuck-sweep:unclaimed","dueAt":"2026-10-28T13:22:29.471Z","intervalSeconds":300},"deadlineAt":null},"qitemId":"qitem-20261028122229-<hex-redacted>","tsCreated":"2026-10-28T12:22:29.471Z","tsUpdated":"2026-10-28T12:22:29.471Z","sourceSession":"red-actor@other-rig","destinationSession":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","priority":"routine","tier":null,"tags":null,"blockedOn":null,"handedOffTo":null,"handedOffFrom":null,"expiresAt":null,"chainOfRecord":null,"body":"S0 alien spoof probe FOR-TEST-ONLY","summary":"S0 alien spoof probe FOR-TEST-ONLY","evidenceRef":null,"humanIntent":null,"humanDetail":null,"replyTo":null,"humanQuestions":null,"humanAnswers":null,"delegatedDecision":null,"closureReason":null,"closureTarget":null,"closureRequiredAt":null,"claimedAt":null,"lastNudgeAttempt":null,"lastNudgeResult":null,"lastNudgeWireResult":null,"lastHeartbeat":null,"resolution":null,"targetRepo":null,"deliveryOutcome":null}
S0: qitemId=qitem-20261028122229-<hex-redacted>
{"pickup":{"state":"unclaimed"},"waiting":{"obligation":"qitem-20261028122229-<hex-redacted>","owner":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","actionableSince":"2026-10-28T12:22:29.471Z","blocker":null,"lastMeaningfulChange":{"id":2,"at":"2026-10-28T12:22:29.472Z"},"liveness":{"subject":"blue-appsec-engineer@defensive-sec-and-red-team","activity":"unknown","needsInput":{"count":0,"reason":null},"confidence":"unknown"},"nextBackstop":{"owner":"blue-appsec-engineer@defensive-sec-and-red-team","mechanism":"queue-stuck-sweep:unclaimed","dueAt":"2026-10-28T13:22:29.471Z","intervalSeconds":300},"deadlineAt":null},"qitemId":"qitem-20261028122229-<hex-redacted>","tsCreated":"2026-10-28T12:22:29.471Z","tsUpdated":"2026-10-28T12:22:29.471Z","sourceSession":"red-actor@other-rig","destinationSession":"blue-appsec-engineer@defensive-sec-and-red-team","state":"pending","priority":"routine","tier":null,"tags":null,"blockedOn":null,"handedOffTo":null,"handedOffFrom":null,"expiresAt":null,"chainOfRecord":null,"body":"S0 alien spoof probe FOR-TEST-ONLY","summary":"S0 alien spoof probe FOR-TEST-ONLY","evidenceRef":null,"humanIntent":null,"humanDetail":null,"replyTo":null,"humanQuestions":null,"humanAnswers":null,"delegatedDecision":null,"closureReason":null,"closureTarget":null,"closureRequiredAt":null,"claimedAt":null,"lastNudgeAttempt":"2026-10-28T12:22:29.484Z","lastNudgeResult":"unroutable: 'blue-appsec-engineer@defensive-sec-and-red-team' has no terminal transport on this daemon and names no registered human — no transport can hold this address (checked: tmux bindings + the human registry). Fix the address, or register the human with `rig gateway human add`.","lastNudgeWireResult":"unroutable: 'blue-appsec-engineer@defensive-sec-and-red-team' has no terminal transport on this daemon and names no registered human — no transport can hold this address (checked: tmux bindings + the human registry). Fix the address, or register the human with `rig gateway human add`.","lastHeartbeat":null,"resolution":null,"targetRepo":null,"deliveryOutcome":null,"destinationClass":"unroutable","ownerNotificationLevel":null}

--- cleanup: stopping scratch daemon ---
S0: daemon stop rc=0
SPOOF-OK pre-fix: forged sender red-ai-red-teamer@defensive-sec-and-red-team accepted (claim recorded, no attestation required)
accepted forged sender: red-ai-red-teamer@defensive-sec-and-red-team
```

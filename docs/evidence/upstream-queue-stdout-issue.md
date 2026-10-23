# Upstream issue draft: queue stdout MUST be pure JSON (covers #44 trailer + #42 receipt)

Filed against: `mvschwarz/openrig` (verified from installed `@openrig/cli@0.6.13`
`package.json` `repository.url = https://github.com/mvschwarz/openrig`).
Single shared issue for heretek-rigs #44 (trailer) + #42 (create receipt):
same stdout-purity principle. Recorded filed URL: see "Filed" line at bottom.

---

## Title

`rig queue` human notices on stdout break `json.load(stdout)`: move trailer +
compact notice (+ create receipt text) to stderr

## Body

**Problem.** Under default flags, three `rig queue` surfaces print human
advisory text to **stdout**, so any agent doing `json.load(stdout)` fails
while `--json` callers are unaffected. All three live in the same
stdout-purity contract; fixing only one leaves stdout impure under some
config.

**Reproduction (byte-exact, `@openrig/cli@0.6.13`, daemon default config).**

Bare `rig queue show qitem-20261022111416-78213c07c3272cbc` (exit 0, 3628
bytes on stdout, 0 bytes on stderr) ends with:

```
}
… (bounded preview — complete body is 815 bytes; full record 3017 JSON bytes: rig queue show 'qitem-20261022111416-78213c07c3272cbc' --full --json)
```

and programmatic parsing fails:

```
>>> json.loads(raw_stdout)
json.JSONDecodeError: Extra data: line 96 column 1 (char 3472)
```

Re-running the identical command with `--json` parses first try
(`qitemId` + full key set present, stderr empty); `rig queue list --json`
likewise parses (21 rows). So the machine-readable path exists — the
default mix is the trap.

**Code cites (`dist/commands/queue.js`, installed 0.6.13).**

1. Bounded-preview trailer, `queue.js:1115-1117`:
   `if (!json && bodyTruncated) { console.log(\`… (bounded preview — …\`) }`
   — stdout, skipped only under `--json`.
2. Compact empty-omitted notice, `queue.js:1118-1124`:
   `if (json) console.error(notice); else console.log(notice)` — stdout
   unless `--json`.
3. Write receipt text, `queue.js:278-286` (`printWriteResult`) +
   `dist/queue-receipt.js:230` (`buildWriteReceipt`): under
   `output.compact` without `--full`, `create`/`update`/etc. print the
   human `projected.text` receipt on stdout; `--json` prints
   `projected.json` (which always carries `qitemId` + `state`,
   `queue-receipt.js:41`). This is the heretek-rigs #42 surface: bare
   `create` yields advisory text instead of the created row, forcing a
   follow-up `show`.

**Precedent for the requested fix (same file).** The `transitions`
notice already goes to stderr: `queue.js:1142`
`console.error(transitionsNotice(...))`, with the comment that the notice
goes to stderr "so it stays visible when the array is piped through jq".
The `create` request-ID line (`queue.js:648`) is likewise already
`console.error`. The ask matches the codebase's own convention.

**Request.** Move stdout notices to stderr so `rig queue …` stdout is
always a single JSON document:

- trailer (`queue.js:1116` `console.log` → `console.error`),
- compact empty-omitted notice (`queue.js:1123` `console.log` branch →
  `console.error`),
- compact write-receipt text (`printWriteResult` non-json branch): emit
  the human receipt on stderr, keep the row JSON on stdout (or keep
  `--json` as the machine path, but make the default stdout parseable).

Human UX is unchanged (same text, same terminal); only the stream
changes, per the file's own transitions precedent. No change to `--full`
semantics requested.

---

## Filed

- https://github.com/mvschwarz/openrig/issues/1806 (filed 2026-10-23)

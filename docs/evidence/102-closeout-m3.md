# M3 red-proofs: writing-skills vendor fix (REQ-CWS)

Branch: `feat/102-closeout`. Spec: `openspec/changes/102-closeout` (REQ-CWS).

## 1. Mechanism (no `specs/` hand-edit, one-rule clean)

- `scripts/generate-rigs.py`: `load_skill_patches` / `apply_skill_patch`
  extended with a fail-closed `replacements:` section (`{file, old, new}`,
  exact-string, exactly-one-hit, skill-dir-confined, no-op/escape/missing
  dies, SKILL.md frontmatter re-validated). Legacy bare-frontmatter call
  shape still accepted; `extract_fm_license` unwraps the normalized shape.
- `fleet/skill-patches/test-driven-development.yaml`: two exact
  replacements on `writing-good-tests.md` that together drop the dangling
  parenthetical while keeping the sentence normative-identical
  ("...tested by the consuming agent's behavior; prose for humans earns
  no test at all."). Split in two so the repair record itself carries zero
  hits of the dangling pattern (REQ-CWS grep-zero over `specs/ + fleet/`
  holds literally).
- Regen bakes the patched bytes into `specs/agents/_shared/...`,
  all rig vendored copies (V21 parity), and re-pins the
  `test-driven-development` tree hash in `fleet/skills-lock.json`.

## 2. RED

Unit (`tests/test_skill_patch_replacements.py`, 8 tests, synthetic /tmp
fixtures only): pre-fix tree errors on the 3 shape tests
(`load_skill_patches` dies demanding frontmatter; applier has no
replacements path).

End-to-end sabotage: patch file moved aside + regen → the exact upstream
hit returns:

```
specs/agents/_shared/skills/test-driven-development/writing-good-tests.md:51:agent's behavior (superpowers:writing-skills); prose for humans earns no
```

(log `/tmp/opencode/102-sabotage-m3.log`). Patch restored + regen →
zero hits again (log `/tmp/opencode/102-dev-regen-m3c.log`).

## 3. GREEN

```
python3 tests/test_skill_patch_replacements.py   # 8/8 OK
grep -rn 'superpowers:writing-skills' specs/ fleet/   # exit 1, zero hits
ls specs/agents/_shared/skills/ | wc -l               # 68
python3 -c "import json; print(len(json.load(open('fleet/skills-lock.json'))['skills']))"  # 68
```

V17 (SKILL.md frontmatter parse over every committed SKILL.md) green in
the final `make verify` (see implementation report); sibling-doc edit
leaves all frontmatter bytes untouched, so the loader stays 68/68 with
no DIAG.

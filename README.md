# audit-memory

A [Claude Code](https://claude.com/claude-code) skill that audits an auto-memory directory by **cross-verifying every checkable claim against live system state** — not by re-reading other memory files — then **deletes** fully-resolved incident memories instead of just annotating them `[FIXED]`.

## Why

Memory files rot in a specific way: they were true when written, and nothing marks them as stale. A future session reads a confident sentence and acts on it long after reality moved on. Worse, a resolved-incident memory ("bug found, root cause confirmed, fix shipped, verified") keeps the shape of a live problem even when annotated closed — a future session absorbs "this is a thing that breaks around here" and starts pattern-matching unrelated symptoms onto a closed story.

This skill fixes both: it verifies claims against the actual running system (git, package manifests, cloud CLIs, databases, HTTP endpoints — whatever the project offers), and it deletes resolved incidents after extracting any durable technique or fact buried in them.

Nothing here is stack-specific — it works the same on an infra repo, a web app, a data pipeline, or a docs project.

## Install

```bash
git clone https://github.com/PRATHAMESHG1234/claude-skill-audit-memory ~/.claude/skills/audit-memory
```

Or copy the folder manually into `~/.claude/skills/audit-memory/` (or a project's `.claude/skills/` for project scope).

## Use

In a Claude Code session, just ask — no slash command needed, the skill auto-triggers on requests like:

- "audit my memory files"
- "is any of this still true?"
- "clean up / prune / tidy memory"
- "cross-check memory against reality"
- "drop completed items from memory"

## What it does

1. **Locate** the memory directory and get oriented on the project (what tools are available and authenticated).
2. **Take stock** — read every memory file, note which claims are checkable (a resource, a config value, a status, a "fix shipped" claim) vs. not (reasoning, technique, preference).
3. **Cross-verify** checkable claims against live state, read-only, in parallel where possible. Every claim gets `CONFIRMED` / `CONTRADICTED (actual: ...)` / `GONE` / `UNVERIFIABLE`.
4. **Classify** every file into one of three buckets:
   - **Durable technique/fact** → keep, correct against verified reality
   - **Fully resolved incident** → extract the durable knowledge, then **delete** the file
   - **Open/unresolved** → keep as-is, correct only what verification proved wrong
5. **Repair fallout** — `scripts/link_check.py` finds dangling `[[wikilinks]]` left by deletions; rewrite each as plain self-contained text.
6. **Rewrite the index** (`MEMORY.md`) from what survives.

## Contents

```
audit-memory/
├── SKILL.md                       # the skill itself
├── references/
│   └── verification-recipes.md    # how to turn a claim into a read-only check, by question type — not by vendor
└── scripts/
    └── link_check.py              # finds dangling [[wikilinks]]/markdown links after deletions
```

## Safety

Every verification step is read-only by design — the skill never runs `create`/`apply`/`delete`/`deploy`/`migrate`/`write` against live infrastructure. Before deleting any memory file it prints the full plan (file → bucket → action → reason) and checks whether the memory directory is under version control, flagging if deletions won't be recoverable.

## License

MIT

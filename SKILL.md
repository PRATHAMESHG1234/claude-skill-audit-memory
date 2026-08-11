---
name: audit-memory
description: "Audit any project's auto-memory directory (the memory/ folder under ~/.claude/projects/) by cross-verifying every claim against live state using whatever tools that project offers — git, package manifests, config files, databases, containers, HTTP endpoints, cloud or platform CLIs — rather than trusting the memory files themselves, then deleting fully-resolved incident memories and rewriting the MEMORY.md index. Works on any stack; it adapts the verification method to the project. Use this whenever the user asks to audit, verify, fact-check, cross-check, clean up, prune, tidy, garbage-collect, or 'ground-truth' memory; whenever they ask whether memories are still accurate or stale; whenever they want completed/resolved/fixed items dropped from memory; and whenever they suspect memory is misleading them or a past session's notes no longer match reality. Use it even if they say something loose like 'my memory files are a mess' or 'is any of this still true?'."
---

# Memory Audit

Memory files rot in a specific, dangerous way: they were true when written. Nothing on the file marks it as having gone stale, so a future session reads a confident sentence — "retries are disabled on that job" — and acts on it, long after someone turned retries back on. Re-reading memory to check memory just launders the original claim.

So the rule that makes this audit worth doing at all: **verify against the live system, not against other memory files.** A recent `Last verified:` line is a claim about the past, not evidence about the present.

There is a second failure mode, subtler and worse. Memory files that narrate a *resolved* incident — problem hit, root cause found, fix shipped, confirmed — keep the shape of a live problem even after someone annotates them `[FIXED]`. A future session reading one absorbs "this is a thing that breaks around here" and starts pattern-matching unrelated current symptoms onto a closed story, or re-investigates ground already covered. The annotation doesn't help; the narrative is what does the damage. That's why this skill **deletes** resolved incidents rather than marking them closed — after lifting out whatever durable knowledge was buried in them.

Nothing here is stack-specific. The audit works the same on an infrastructure repo, a web app, a data pipeline, or a docs project; only the tools you verify *with* change.

## Phase 0 — Locate the memory directory

Memory usually lives at `~/.claude/projects/<project>/memory/` with an index at `MEMORY.md`. If your system prompt's auto-memory section names a different path, that wins. If the user named a directory, use theirs. If you can't find one, say so and stop rather than auditing some other directory that happens to contain markdown.

Then get oriented on the *project*, because that determines what "live state" even means here. Look at the repo root — remotes, manifests, infra files, compose files, CI config — and check which relevant tools are installed *and* authenticated. This has to happen before Phase 2, since it tells you which claims you have any means of checking at all. `references/verification-recipes.md` opens with a discovery sweep you can run as-is.

Whatever you find, don't assume a stack. A project with no cloud CLI and no database is still auditable through git, manifests, config, and the filesystem.

## Phase 1 — Take stock

- List the directory (including sizes and mtimes — a large or ancient file is a hint, not a verdict).
- Read `MEMORY.md` end to end.
- Read every topic file. Skim is fine for long ones, but you need to have actually seen each file; you can't classify what you haven't read.

As you read, build a working list. For each file note: what it asserts, and which of those assertions are **checkable** — i.e. have a counterpart in the live world you could go look at.

A claim is checkable when reality could contradict it: an identifier or name of something that exists somewhere, a config value, a feature flag, an env var, a version pin, a schema column, a file path, a function signature, an endpoint, a permission, a "currently enabled/disabled" status, a "we're blocked on X" status, an open ticket or PR, or an assertion that some fix already shipped.

A claim is *not* checkable, and doesn't need verification: reasoning about why a decision was made, a technique or query pattern, a gotcha about how a tool behaves, a preference the user stated.

## Phase 2 — Cross-verify against reality

Go check the checkable claims. All of them — this is the phase that gives the audit its value, and skipping claims because they "look fine" reintroduces exactly the trust you're here to remove.

**Fan out.** Verification is naturally parallel: each claim is an independent lookup, and they're slow (network calls, CLI round-trips). Group the checkable claims into batches by tool or domain — one batch per memory file, or one per subsystem, whichever gives you chunks of roughly comparable size — and dispatch them to subagents concurrently in a single turn. Give each subagent the exact claims to check, tell it to run read-only commands only, and ask it back for a compact verdict per claim: `CONFIRMED` / `CONTRADICTED (actual: ...)` / `GONE (resource no longer exists)` / `UNVERIFIABLE (reason)`. If subagents aren't available, do the checks inline — batch related lookups into single commands so you're not paying a round-trip per claim.

**Adapt the check to whatever this project actually offers.** The principle is constant — find the authoritative source for that class of fact and query it — while the command is entirely project-dependent. Read `references/verification-recipes.md` when deciding how to check a claim: it's organized by the *question* you're asking (does it exist? is the value still X? did the change land? is it still failing? is it still open?), with a cheat sheet translating each question into git, package, database, container, HTTP, filesystem, and cloud-CLI terms. Note especially that verifying live state means asking the running system, not reading the code or config that was supposed to configure it — drift between declared intent and actual state is the main thing you're hunting.

**Read-only, always.** Verification describes the world; it must not change it. Prefer `describe`/`get`/`list`/`show`/`--dry-run`. Never run a command that creates, deletes, mutates, deploys, or costs money — even if a memory file says a fix "should be applied." Applying fixes is a separate job the user can ask for separately.

**`UNVERIFIABLE` is a real answer.** Missing credentials, a decommissioned account, a tool you don't have — record it and move on. Don't guess, and don't downgrade an unverifiable claim to "probably still true." Say plainly in the final report which claims you couldn't reach; that's useful information about the audit's coverage.

Carry every verdict into Phase 3. The verdicts, not the files' own confidence, decide what happens next.

## Phase 3 — Classify every file into exactly one bucket

Every file lands in one bucket. If a file feels like it straddles two, that's usually a sign it should be split — pull the durable part out into its own file (or an existing reference file) and let the remainder be classified on its own.

**Bucket A — Durable technique or fact.** Reusable knowledge with no expiry: a lookup table of resource IDs, a query pattern that took effort to get right, a gotcha about how a tool misbehaves, an architecture note, a naming convention, a "here's how to check X" recipe.
→ **Keep.** Apply Phase 2's corrections: where a claim came back `CONTRADICTED`, rewrite it to the actual value; where `GONE`, remove that row or note. Leave a light `Verified <date>` marker on facts you actually checked so a future audit knows what was covered — and keep it honest by not marking things you didn't check.

**Bucket B — Fully resolved incident.** All four must hold: the problem was identified, the root cause is confirmed (not merely suspected), the fix shipped, and the fix was verified — with nothing left open, no follow-up, no "we should also…". If the fix is described but you couldn't confirm it landed, verify it in Phase 2 before classifying; if it still can't be confirmed, it belongs in Bucket C.
→ **Extract, then delete.** Read the file once more hunting for anything durable hiding in the narrative — the command that diagnosed it, the setting nobody knew existed, the reason the system behaves the way it does. Move that into the relevant Bucket A file as a standalone statement of fact, phrased to stand on its own without the incident. The rewrite is small but it's the whole trick: *"during the outage last month we discovered the worker needs the config reloaded after a flag change"* becomes *"flag changes don't take effect until the worker reloads config; restart it or the old value persists."* Same knowledge, no story. Then delete the incident file.

Do not compromise here by marking it `[RESOLVED]` and keeping it. A resolved-incident file that survives as an annotation is still a story about something being broken, sitting in a future session's context, waiting to be pattern-matched onto an unrelated symptom. Deleting it is the whole point; the durable extract is how you avoid losing anything of value.

**Bucket C — Open, unresolved, or decision pending.** An active investigation, a known-broken thing not yet fixed, a decision the user hasn't made, a partial fix, a "revisit when Y ships."
→ **Keep as-is, with a light touch.** Correct only what Phase 2 proved wrong, and note the correction. Don't rewrite the framing, don't editorialize about staleness, don't declare something resolved because it looks quiet — an unverified guess that a problem went away is worse than an honest open question. If verification showed the problem *is* in fact fixed, that reclassifies it into Bucket B and it gets extracted and deleted.

## Phase 4 — Show the plan, then execute

Before touching anything, print a compact table: file → bucket → action → one-line reason, plus the list of extracts you're moving and where they're going. Then carry it out in the same run — no need to wait for approval. The plan exists so the user can see and challenge your reasoning, not so the work stalls.

Two things worth doing before deleting: check whether the memory directory is under version control (`git -C <dir> rev-parse` / `git status`), and mention in the plan whether deletions are recoverable. If it isn't tracked and you're deleting more than a couple of files, that's worth flagging in one sentence — the user may want a copy first.

## Phase 5 — Repair the fallout

Deleting files breaks references. Fix them:

```bash
python3 scripts/link_check.py <memory-dir>
```

This reports every `[[wikilink]]` and relative markdown link in the surviving files that points at a file that no longer exists.

Rewrite each dangling reference as **plain, self-contained text** — not a link to some other file, and not a link with the brackets stripped off. The sentence has to still make sense to a reader who never saw the deleted file, which means inlining the one fact the reference was carrying: `for background see [[worker-stall-incident]]` becomes `flag changes require a worker restart to take effect`. If you can't inline it because the fact no longer exists anywhere, Phase 3's extraction missed something — recover it from the deleted file before it's gone for good.

Re-run the script after editing; it should come back clean.

## Phase 6 — Rewrite MEMORY.md

Rebuild the index from what actually remains, rather than editing the old one — editing tends to leave ghost entries for deleted files.

- One line per surviving file: `- [Title](file.md) — one-line hook`, under ~150 chars.
- Under 200 lines total. If you're over, the index is carrying detail that belongs in the topic files.
- Group by theme if there are enough entries to warrant headings.

Include a short standing note near the top so future sessions understand why the directory looks the way it does:

> **Note on resolved incidents.** Fully-resolved incidents are deliberately not kept here. Durable facts and techniques learned from them are folded into the reference files above; the incident narratives themselves are deleted. Keeping them biases future sessions toward re-litigating closed questions and toward reading current symptoms as recurrences of old ones, instead of checking present state fresh.

## Report back

Close with a brief summary — no ceremony:

- Counts: files read, claims verified, confirmed / contradicted / unverifiable.
- What was contradicted and what it actually is now. This is usually the most valuable part; lead with it.
- What was deleted and where each one's durable extract landed.
- Dangling links repaired.
- Anything you couldn't verify, and what would be needed to verify it.

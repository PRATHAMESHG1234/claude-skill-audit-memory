# Contributing

Issues and PRs welcome.

## Useful contributions

- **New verification recipes** — `references/verification-recipes.md` is organized by *question type* (does it exist? is the value still X? did the change land? is it still failing? is it still open?), not by vendor. If you hit a class of claim that doesn't map cleanly onto the existing five, or a tool/ecosystem row missing from the cheat sheet, add it there.
- **`scripts/link_check.py` improvements** — edge cases in link parsing (new link syntaxes, false positives/negatives on candidate resolution), or a companion script if a similar mechanical check would help (e.g. a stale-date flagger).
- **SKILL.md clarity/behavior fixes** — if you run the skill and it misclassifies a file, skips a verifiable claim, or does something the phases don't actually justify, that's a bug in the instructions, not just a suggestion.

## Ground rules

- **Stay stack-agnostic.** The skill and its reference doc intentionally organize around the *kind of question* being asked, not a specific vendor or language. If your addition only makes sense for one ecosystem, put the specifics in the ecosystem cheat-sheet table, not the main flow.
- **Read-only by default.** Nothing this skill does should be able to mutate live state. Any addition that runs `create`/`apply`/`delete`/`deploy`/`migrate`/`write` needs a very good reason and should be called out loudly, not slipped into a verification step.
- **No real account/company/infra data in examples.** Keep examples generic (`<host>`, `example-service`, etc.) — this repo is meant to be cloned and used as-is by anyone.
- **Keep SKILL.md's frontmatter description trigger-rich.** If you change what the skill covers, update the `description` field too — that's what drives auto-invocation matching.

## Testing a change

There's no test suite — this is a prompt/instructions skill, not code (aside from `link_check.py`, which you can run directly: `python3 scripts/link_check.py <memory-dir>`). To validate a SKILL.md change, install it locally (`git clone` into `~/.claude/skills/audit-memory`, or symlink your working copy there) and run it against a real memory directory to confirm the behavior actually changed as intended.

## Opening a PR

Small, focused PRs are easier to review than large rewrites. Explain *why* in the description if the change isn't self-evident — same standard the skill itself asks for when writing memory.

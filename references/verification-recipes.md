# Verification recipes

How to turn a memory claim into a read-only check against live state, in any project.

This is organized by **the kind of question you're asking**, not by vendor — because the question is what stays constant. "Does this thing still exist?" is the same problem whether the thing is a cloud queue, a database column, a config key, or a function. Find your question below, then use the ecosystem table at the end to fill in the actual command for whatever this project happens to use.

Two rules cut across everything:

1. **Read-only.** Every check here describes state. If you reach for `create`, `apply`, `delete`, `deploy`, `migrate`, `install`, or `write`, stop — that's remediation, not verification, and it's a separate job.
2. **Query the authoritative source.** A claim about a running system is verified by asking the running system, not by reading the code or config that was supposed to configure it. Declared intent and actual state drift apart constantly — drift is precisely what you're hunting.

Contents: [Discovery](#0-discovery) · [Does it exist?](#1-does-it-exist) · [Is the value still X?](#2-is-the-value-still-x) · [Did the change land?](#3-did-the-change-land) · [Is it still failing?](#4-is-it-still-failing) · [Is this still open?](#5-is-this-still-open) · [Ecosystem cheat sheet](#ecosystem-cheat-sheet) · [Unverifiable](#when-a-claim-is-unverifiable)

---

## 0. Discovery

Before verifying anything, work out what this project actually gives you. You can't pick a check until you know which authoritative sources are reachable.

```bash
ls -a                                      # config files reveal the stack
git remote -v && git log --oneline -5
cat package.json pyproject.toml go.mod Cargo.toml Gemfile composer.json 2>/dev/null | head -60
ls *.tf docker-compose.y*ml Makefile .github 2>/dev/null
```

Then check which tools are present *and authenticated* — a binary you can't authenticate with is not a verification path:

```bash
command -v git gh aws gcloud az kubectl docker psql mysql redis-cli terraform jq curl 2>/dev/null
```

Authentication matters as much as availability, and so does *which* environment you're pointed at. A claim verified against staging is not verified against production; a cloud resource "missing" from the wrong account or project is not missing. Establish your context first (whoami / current-project / current-context / current branch) and state it in the report.

If the project has none of these — it's a plain document repo, say — most claims will be filesystem and git claims, and that's fine. The audit is still worth doing.

---

## 1. Does it exist?

Claims naming a specific thing: a resource, table, column, file, function, endpoint, index, env var, secret, job.

**Approach:** ask the system that owns the namespace to describe that one thing by name. Prefer a targeted `describe`/`show`/`get` over listing everything and grepping — listings paginate and truncate, and a thing missing from page one is not a thing that doesn't exist.

**Three outcomes, and they're different:**

- Found → `CONFIRMED`
- Authoritatively absent (the system says "no such thing") → `GONE`
- You couldn't ask (no access, no credentials, wrong environment) → `UNVERIFIABLE`, never `GONE`

**The trap:** proving absence is much harder than proving presence. Before reporting `GONE`, confirm you queried the right region/project/namespace/schema/branch, that your search wasn't silently filtered (ignore rules, default excludes, permission-scoped listings), and that the thing wasn't renamed rather than removed. Most false `GONE` verdicts are lookups in the wrong context.

---

## 2. Is the value still X?

Claims asserting a specific setting: a timeout, a replica count, a version pin, a feature flag, a permission, a retention period, a connection limit.

**Approach:** read the current value from the authoritative source and compare literally. Report the actual value in the verdict — `CONTRADICTED (actual: 30s, memory said 5s)` is useful; `CONTRADICTED` alone forces someone to redo your work.

**The trap specific to this class:** the same setting usually exists in several places that disagree — declared vs. deployed vs. running, manifest vs. lockfile vs. installed, default vs. per-environment override. Decide which one the memory file was talking about, check *that* one, and name the source in your verdict. If two sources disagree with each other, that's a finding worth reporting on its own; it often explains the original confusion.

---

## 3. Did the change land?

Claims that a fix was applied, code was removed, a migration ran, a setting was corrected, a deploy went out. These are the claims that decide whether a file is a resolved incident (delete) or still open (keep) — so they deserve the most care.

**Approach — look for evidence in the record, not the intent:**

- **In code:** search history for the commit where the string entered or left the codebase. History is proof; current-state absence alone is weak, because the code may never have been there in that form.
- **In infrastructure:** compare live config against what the fix claimed, then check a last-modified/updated timestamp to see whether anything was touched at all.
- **In a database:** query the migrations/versions table, then confirm the resulting schema object actually exists — a recorded migration that failed halfway is common.
- **In a service:** hit the version or health endpoint and compare against the version the fix shipped in.

**The trap:** config looking correct is not the same as the problem being solved. A permission can be attached and errors continue for an unrelated reason. Where you can, pair a config check with a behavior check (section 4) before calling something resolved — that pairing is exactly what separates "fix shipped" from "fix shipped and verified," which is the line between keeping a memory and deleting it.

---

## 4. Is it still failing?

Claims about ongoing behavior: errors, latency, crashes, retries, a job that keeps timing out.

**Approach:** look at recent observable behavior over a bounded window — logs filtered to the error signature, event streams, restart counts, health endpoints, test or CI runs. Bound the window explicitly (last hour, last day) and say which window you used; "no errors" means nothing without a timeframe.

**The trap in both directions:** silence can mean the fix worked, or that the code path stopped being exercised, or that logging changed, or that you're reading the wrong stream. Conversely, errors in the window may predate the fix. Check *when* within the window the events fall relative to when the fix landed. If you can't tell, say `UNVERIFIABLE` — a wrong "resolved" verdict causes a deletion, and deletions are the one action here you can't take back.

---

## 5. Is this still open?

Claims about tracked work or decisions: an open ticket, an unmerged PR, a pending decision, a blocked dependency, an upstream bug.

**Approach:** query the tracker for current status by ID. If the item lives somewhere you can't reach (a vendor's board, an internal tool, a conversation), that's `UNVERIFIABLE` — and worth flagging to the user, since these are usually the fastest claims for *them* to check.

**The trap:** a closed ticket doesn't automatically mean the underlying problem is resolved — items get closed as stale, duplicate, or won't-fix. Read the resolution before letting a closed status reclassify a memory into the delete bucket.

---

## Ecosystem cheat sheet

Fill in the command for whatever this project uses. Pick the row matching your question from above.

| Question | Cloud CLI (AWS / GCP / Azure) | Git & forge | Packages | Database | Containers / K8s | Filesystem & code | HTTP service |
|---|---|---|---|---|---|---|---|
| **Context** — where am I? | `aws sts get-caller-identity` · `gcloud config list` · `az account show` | `git remote -v`, `git branch --show-current`, `gh auth status` | `node -v`, `python3 -V`, `go version` | `SELECT current_database(), current_user` | `kubectl config current-context`, `docker context ls` | `pwd`, `git rev-parse --show-toplevel` | base URL from project config |
| **Exists?** | `describe-*` / `get-*` / `head-*` by name (`aws lambda get-function-configuration`, `gcloud storage buckets describe`, `az resource show`) | `git ls-files "*name*"`, `git cat-file -e <rev>:<path>` | `npm ls <pkg> --depth=0`, `pip show <pkg>`, `go list -m <mod>` | `\d+ <table>`, `information_schema.columns`, `pg_indexes` | `kubectl get <kind> <name>`, `docker image inspect <img>` | `ls -la <path>`, `find . -name '<pat>' -not -path '*/node_modules/*'` | `curl -sS -o /dev/null -w '%{http_code}' <url>` |
| **Value still X?** | same `describe-*` plus `--query`/`--format` to pull the field | `git config --get <key>`, file contents at a rev | manifest vs. lockfile vs. installed — check all three | `SHOW <setting>`, `pg_get_constraintdef`, column types | `kubectl get deploy X -o jsonpath='{...}'`, `docker compose config` | `rg -n 'KEY_NAME'` across code *and* config, `jq '.a.b' config.json` | `curl -sSI <url>` for headers |
| **Change landed?** | resource's last-modified/updated timestamp | `git log -S'<string>' --oneline`, `git log --grep='<kw>'`, `gh pr view <n> --json state,mergedAt` | lockfile diff, installed version vs. claimed | migrations table (`schema_migrations`, `alembic_version`) + schema object exists | image tag / `kubectl rollout history` | `git log -S` beats reading the file | `/version` or `/health` endpoint |
| **Still failing?** | log query filtered to the signature over a bounded window | `gh run list --branch main --limit 5` | `npm audit`, `pip check` | error/job tables, `pg_stat_activity` | `kubectl get pods` restart counts, `kubectl get events --sort-by=.lastTimestamp \| tail -20` | local test run | repeated health probe |
| **Still open?** | provider console (often unreachable → unverifiable) | `gh issue view <n> --json state,closedAt`, `gh pr list --state open` | upstream issue link | — | — | TODO/FIXME comments via `rg` | — |

Notes that bite people:

- Cloud CLIs are region/project/subscription-scoped. Wrong scope produces convincing false negatives.
- `AccessDenied` is `UNVERIFIABLE`, not `CONTRADICTED`. Very different findings.
- Cloud `describe` output is verbose — project just the field you need (`--query`, `--format`, `| jq`) to keep responses small.
- For databases, use a read-only connection where one exists, and name the environment you connected to.
- For HTTP, only `GET`/`HEAD`, and only against endpoints the project already documents. Don't probe third-party APIs a memory merely mentions.
- For code, grep proves presence cleanly; proving absence needs history (`git log -S`) plus a check that renames didn't fool you.

---

## When a claim is unverifiable

Mark `UNVERIFIABLE` and give the reason in one line. Common ones: no credentials for that environment; the tool isn't installed; the thing lives in a system you have no access to; the claim describes a past event with no surviving trace (logs rotated out).

Resist two temptations:

- **Don't infer confirmation from adjacent evidence.** "The config declares it" is not "the system does it." That inference is the exact failure the audit exists to prevent.
- **Don't delete a memory because you couldn't check it.** Unverified is not false. An audit that quietly drops what it couldn't reach is worse than one that says so out loud — the user can usually check those few items in seconds if you tell them which they are.

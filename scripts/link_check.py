#!/usr/bin/env python3
"""Find dangling references in a memory directory.

Scans every markdown file for [[wikilinks]] and relative markdown links, and
reports the ones pointing at files that no longer exist -- which is what happens
after an audit deletes resolved-incident files.

Usage:
    python3 link_check.py <memory-dir> [--json]

Exit code is 0 when clean, 1 when dangling references remain, so it can be used
as a gate after editing.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote

# [[target]] or [[target|alias]] or [[target#heading]]
WIKILINK = re.compile(r"\[\[([^\[\]]+?)\]\]")
# [text](target) -- skip absolute URLs, mailto, and pure anchors
MDLINK = re.compile(r"(?<!!)\[([^\]\[]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
SKIP_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "tel:", "#", "data:")


def strip_code(text: str) -> str:
    """Blank out fenced and inline code so examples in docs aren't flagged."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    return text


def candidates(target: str, base: Path, root: Path):
    """Plausible on-disk paths for a link target."""
    target = unquote(target.split("#")[0].split("|")[0].strip())
    if not target:
        return []
    paths = []
    for parent in (base, root):
        p = (parent / target).resolve()
        paths.append(p)
        if not p.suffix:
            paths.append(p.with_suffix(".md"))
            paths.append(p / "index.md")
    return paths


def scan(root: Path):
    files = sorted(p for p in root.rglob("*.md") if p.is_file())
    known = {p.resolve() for p in files}
    # also allow non-markdown files that exist on disk
    known |= {p.resolve() for p in root.rglob("*") if p.is_file()}

    broken, total = [], 0
    for f in files:
        try:
            body = strip_code(f.read_text(encoding="utf-8", errors="replace"))
        except OSError as e:
            print(f"warning: could not read {f}: {e}", file=sys.stderr)
            continue
        for lineno, line in enumerate(body.splitlines(), 1):
            found = [(m.group(1), "wikilink") for m in WIKILINK.finditer(line)]
            for m in MDLINK.finditer(line):
                tgt = m.group(2)
                if tgt.startswith(SKIP_SCHEMES) or tgt.startswith("/"):
                    continue
                found.append((tgt, "markdown"))
            for target, kind in found:
                total += 1
                if not any(c in known or c.exists() for c in candidates(target, f.parent, root)):
                    broken.append({
                        "file": str(f.relative_to(root)),
                        "line": lineno,
                        "target": target.split("|")[0].split("#")[0].strip(),
                        "kind": kind,
                        "text": line.strip()[:160],
                    })
    return files, total, broken


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("directory", help="memory directory to scan")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = ap.parse_args()

    root = Path(args.directory).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    files, total, broken = scan(root)

    if args.json:
        print(json.dumps({
            "directory": str(root),
            "files_scanned": len(files),
            "links_checked": total,
            "dangling": broken,
        }, indent=2))
        return 1 if broken else 0

    print(f"Scanned {len(files)} markdown file(s), {total} link(s) in {root}")
    if not broken:
        print("No dangling references. Clean.")
        return 0

    print(f"\n{len(broken)} dangling reference(s):\n")
    by_file: dict[str, list] = {}
    for b in broken:
        by_file.setdefault(b["file"], []).append(b)
    for fname, items in sorted(by_file.items()):
        print(f"  {fname}")
        for b in items:
            print(f"    line {b['line']}: -> {b['target']}  ({b['kind']})")
            print(f"      {b['text']}")
        print()
    print("Rewrite each as plain, self-contained text that inlines the fact the")
    print("reference was carrying -- don't repoint it at another file.")
    return 1


if __name__ == "__main__":
    sys.exit(main())

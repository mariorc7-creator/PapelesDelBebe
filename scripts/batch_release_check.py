#!/usr/bin/env python3
"""Safe batched content release preflight.

Read-only; never deploys or modifies site files. Exits nonzero on invariant
regressions. A source/legality review remains a separate human approval.
"""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SEO_PATTERNS = {
    "canonical": re.compile(r'<link\b(?=[^>]*\brel=["\x27]canonical["\x27])[^>]*\bhref=["\x27]([^"\x27]+)', re.I),
    "robots": re.compile(r'<meta\b(?=[^>]*\bname=["\x27]robots["\x27])[^>]*\bcontent=["\x27]([^"\x27]+)', re.I),
    "viewport": re.compile(r'<meta\b(?=[^>]*\bname=["\x27]viewport["\x27])[^>]*\bcontent=["\x27]([^"\x27]+)', re.I),
    "title": re.compile(r'<title\b[^>]*>(.*?)</title>', re.I|re.S),
    "h1": re.compile(r'<h1\b[^>]*>', re.I),
}
class Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.urls = []
        self.tags = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] = self.tags.get(tag, 0) + 1
        if attrs.get("id"):
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.urls.append(attrs["href"])

def git(*args, root=ROOT):
    result = subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True)
    return result.stdout

def inspect_batch(base, root=ROOT):
    if not re.fullmatch("[0-9a-f]{40}", base):
        raise ValueError("Use an immutable 40-character SHA for release baseline")
    changed = [line for line in git("diff", "--name-only", base, "HEAD", "--",root=root).splitlines() if line]
    problems = []
    pages = []
    if not changed:
        problems.append("Empty release: no changed files")
    for path in changed:
        if path.startswith("../") or path.startswith("/"):
            problems.append(f"Unsafe file path {path}")
            continue
        if not path.endswith("/index.html") and path != "index.html":
            if path in ("vercel.json", "sitemap.xml", "robots.txt") or path.endswith(".css") or path.endswith(".js"):
                problems.append(f"Non-content change {path} requires separate technical release")
            continue
        current_path = root / path
        if not current_path.is_file():
            problems.append(f"Page missing: {path}")
            continue
        now = current_path.read_text(encoding="utf-8")
        try:
            before = git("show", f"{base}:{path}",root=root)
        except subprocess.CalledProcessError:
            before = None
        parsed = Structure()
        parsed.feed(now)
        if parsed.tags.get("h1",0) != 1:
            problems.append(f"{path}: expected exactly one H1")
        if len(parsed.ids) != len(set(parsed.ids)):
            problems.append(f"{path}: duplicated HTML IDs")
        if parsed.tags.get("main", 0) != 1 or parsed.tags.get("header", 0) != 1:
            problems.append(f"{path}: missing main/header")
        if parsed.tags.get("footer",0) != 1:
            problems.append(f"{path}: missing footer")
        for name in ("canonical", "viewport", "title"):
            match = SEO_PATTERNS[name].search(now)
            if not match or not match.group(1).strip():
                problems.append(f"{path}: missing {name}")
        canonical = SEO_PATTERNS["canonical"].search(now)
        if canonical and not canonical.group(1).startswith("https://www.papelesdelbebe.es/"):
            problems.append(f"{path}: unexpected canonical host")
        if re.search(r'<meta\b[^>]*\bcontent=["\x27]noindex', now, re.I):
            problems.append(f"{path}: accidental noindex")
        for url in parsed.urls:
            if url.strip().lower().startswith(("javascript:", "http://")):
                problems.append(f"{path}: unsafe/insecure link: {url[:80]}")
        if before is not None:
            for name in ("canonical", "robots", "viewport"):
                old_match = SEO_PATTERNS[name].search(before)
                new_match = SEO_PATTERNS[name].search(now)
                if old_match and (not new_match or old_match.group(1) != new_match.group(1)):
                    problems.append(f"{path}: changed {name}; separate SEO review required")
            for marker in ('<header', '<footer', '<main'):
                previous = before.lower().count(marker)
                current = now.lower().count(marker)
                # Permit repairing one missing semantic wrapper without accepting
                # removals, duplicates or changes to an existing wrapper count.
                if previous != current and not (previous == 0 and current == 1):
                    problems.append(f"{path}: structural marker changed {marker}")
        pages.append(path)
    return {
        "schema_version": 1,
        "mode": "read_only",
        "base_sha": base,
        "changed_files": changed,
        "changed_pages": pages,
        "problem_count": len(problems),
        "problems": problems,
        "technical_checks_passed": not problems,
        "official_content_verified": False,
        "editorial_approval": False,
        "mobile_visual_qa_verified": False,
        "production_deploy_authorized": False
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    report=inspect_batch(a.base,a.root)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Batch checked: {len(report['changed_pages'])} pages; {len(report['problems'])} problems. No deployment.")
    for problem in report["problems"]:
        print("BLOCK: "+problem)
    return 1 if report["problems"] else 0

if __name__=="__main__":
    sys.exit(main())

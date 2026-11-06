#!/usr/bin/env python3
"""Prove byte-perfect apply/rollback for a proposed editorial batch in a temp directory.

This test NEVER writes to checkout HTML, Git branches, deployments or production.
It proves reversible *local file changes*, not deployment rollback.
"""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path
from superagente_editorial_preview import build

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def prove(root, manifest):
    root = Path(root).resolve()
    proposal = build(root, manifest)
    changes = manifest["changes"]
    results = []
    with tempfile.TemporaryDirectory(prefix="superagente-rollback-") as tmp:
        sandbox = Path(tmp)
        for item in changes:
            rel = Path(item["path"])
            original_path = (root / rel).resolve()
            source_bytes = original_path.read_bytes()
            staged = sandbox / rel
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(source_bytes)
            before = staged.read_bytes()
            old = item["search"].encode("utf-8")
            new = item["replacement"].encode("utf-8")
            if before.count(old) != 1:
                raise ValueError(f"stale or ambiguous byte anchor: {rel}")
            after = before.replace(old, new, 1)
            if after == before:
                raise ValueError(f"no change: {rel}")
            staged.write_bytes(after)
            if staged.read_bytes() != after:
                raise RuntimeError(f"staged edit mismatch: {rel}")
            if after.count(new) != 1:
                raise ValueError(f"replacement not unique: {rel}")
            restored = staged.read_bytes().replace(new, old, 1)
            staged.write_bytes(restored)
            if staged.read_bytes() != before or digest(restored) != digest(before):
                raise RuntimeError(f"rollback mismatch: {rel}")
            if original_path.read_bytes() != source_bytes:
                raise RuntimeError(f"checkout modified: {rel}")
            results.append({"path": str(rel), "original_sha256": digest(before),
                            "modified_sha256": digest(after),
                            "restored_sha256": digest(restored),
                            "byte_exact_rollback": True})
    return {"package_id": manifest.get("package_id"), "scope": "isolated_local_file_reversal_only",
            "status": "local_rollback_passed", "production_rollback_tested": False,
            "publishable": False, "proposal_validated": proposal["status"] == "review_required",
            "files": results,
            "warning": "Passing this check never authorizes merge, deploy or production rollback."}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument("--manifest", type=Path, default=Path("superagente/proposals/editorial-2026-11-06-first-five.json"))
    p.add_argument("--output", type=Path, default=Path("superagente/proposals/rollback-proof.json"))
    args = p.parse_args()
    root = args.root.resolve()
    manifest_path = args.manifest if args.manifest.is_absolute() else root / args.manifest
    result = prove(root, json.loads(manifest_path.read_text(encoding="utf-8")))
    output = args.output if args.output.is_absolute() else root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Byte-exact sandbox rollback proven for {len(result['files'])} files; production untouched")

if __name__ == "__main__":
    main()

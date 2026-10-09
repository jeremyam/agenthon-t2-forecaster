"""Seal a Track 2 descriptor and pack submission.zip.
Usage: python make_submission.py --phase dev|final --registry ghcr.io --repository jeremyam/agenthon-t2-forecaster --digest sha256:<64hex>
Team Key is read from /workspace/agenthon/.team-key by the toolkit (never printed)."""
import argparse, json, subprocess, pathlib
from qfbench2_common.contracts.descriptor import seal_descriptor_digest, SubmissionDescriptor
ap = argparse.ArgumentParser()
ap.add_argument("--phase", choices=["dev", "final"], required=True)
ap.add_argument("--registry", required=True); ap.add_argument("--repository", required=True)
ap.add_argument("--digest", required=True); ap.add_argument("--pack", action="store_true")
a = ap.parse_args()
d = {"schema_version": "1.1.0", "interface_version": "2.0",
     "competition_id": f"agenthon2026-forecasting-{a.phase}",
     "team_id": "team-2a0c476e37f7bfec07e859f3e536e673",  # qfbench2 submission alias --team-number 717
     "track": "forecasting", "phase": a.phase, "category": "api",
     "image": {"registry": a.registry, "repository": a.repository, "digest": a.digest},
     "image_access": "public", "models": [], "license": "MIT", "descriptor_digest": "sha256:" + "0" * 64}
d = seal_descriptor_digest(d)
SubmissionDescriptor.from_mapping(d)  # raises if invalid
out = pathlib.Path(f"submission.{a.phase}.json"); out.write_text(json.dumps(d, indent=2) + "\n")
print("wrote", out, d["descriptor_digest"])
if a.pack:
    subprocess.run(["qfbench2", "submission", "pack", "--descriptor", str(out), "--team-number", "717",
                    "--team-key-file", "/workspace/agenthon/.team-key", "--out", f"submission.{a.phase}.zip", "--force"], check=True)

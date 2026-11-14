"""Export a real-cell agent run in the published traces format (robot-api-speed/traces/<run>/), offline, read-only."""
import base64, glob, io, json, os, re, shutil, sys
from PIL import Image

RUNS = "/home/shao/robot-api-real/agent-runs"
OUT = "/home/shao/robot-api-real/robot-api-dsk/docs/demos/traces"

def scrub(x):
    if isinstance(x, str):
        if x.startswith("data:image/") and len(x) > 1000:
            kb = len(x) * 3 // 4 // 1024
            return f"<image omitted ({kb} KB): see views/>"
        return x
    if isinstance(x, list):
        return [scrub(v) for v in x]
    if isinstance(x, dict):
        d = {k: scrub(v) for k, v in x.items()}
        if "encrypted_content" in d and d["encrypted_content"]:
            d["encrypted_content"] = "<encrypted reasoning, omitted>"
        for k in ("creator_user_id", "creator_account_id", "account_id", "user_id", "email"):
            if k in d and isinstance(d[k], str):
                d[k] = "(removed)"
        return d
    return x

def jpeg(src, dst, q=80, maxw=960):
    im = Image.open(src)
    im = im.convert("RGB")
    if max(im.size) > maxw:
        s = maxw / max(im.size)
        im = im.resize((round(im.size[0] * s), round(im.size[1] * s)), Image.LANCZOS)
    im.save(dst, quality=q, optimize=True)

def main(tag):
    run = os.path.join(RUNS, tag)
    out = os.path.join(OUT, tag)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "views"))
    for f in ("TIMELINE.md", "profile.json", "verdict.json", "meta.json", "timeline.jsonl"):
        shutil.copy2(os.path.join(run, f), os.path.join(out, f))
    shutil.copy2(os.path.join(run, "workspace", "AGENTS.md"), os.path.join(out, "AGENTS.md"))
    shutil.copy2(os.path.join(run, "workspace", ".robot", "events", "queue.jsonl"), os.path.join(out, "queue.jsonl"))
    rolls = sorted(glob.glob(os.path.join(run, "codex", "home", "sessions", "**", "rollout-*.jsonl"), recursive=True))
    for i, p in enumerate(rolls, 1):
        with open(os.path.join(out, f"rollout-{i}.jsonl"), "w") as w:
            for line in open(p, errors="replace"):
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                w.write(json.dumps(scrub(d)) + "\n")
    n = 0
    for p in sorted(glob.glob(os.path.join(run, "workspace", ".robot", "views", "*.png"))):
        jpeg(p, os.path.join(out, "views", os.path.basename(p)[:-4] + ".jpg"))
        n += 1
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(out) for f in fs)
    print(tag, len(rolls), "threads", n, "views", f"{size/1e6:.1f} MB")

if __name__ == "__main__":
    for t in sys.argv[1:]:
        main(t)

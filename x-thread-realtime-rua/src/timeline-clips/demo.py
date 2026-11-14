"""The combined pipelining demo: title, animated stages (stages.json), comparison, cups-02 and towel-fold-18 live.

    python demo.py STAGES_JSON OUT.mp4 [--stills DIR]
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
from render import F, hx, W, H, BG, PANEL, TRACK, GRID, TEXT, MUTED, FAINT, ROBOT_A, ROBOT_B, FAIL, THINK, TOOL, REPORT, QUEUE

FPS = 30
GEN = hx("#c9bcff")
IMG = hx("#ff7eb6")
STATE_COL = {"thinking": THINK, "waiting": THINK, "generating": GEN, "tool": TOOL, "images": IMG, "image": IMG,
             "report": REPORT, "idle": None}
KIND_COL = {"modelled": hx("#7d8aa3"), "modeled": hx("#7d8aa3"), "measured": ROBOT_B, "projected": hx("#f6b93b")}


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x) if x < 1 else 1.0


def ease_io(x):
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * math.cos(math.pi * x)


def lerp(a, b, k):
    return a + (b - a) * k


def lerpc(a, b, k):
    return tuple(int(round(lerp(x, y, k))) for x, y in zip(a, b))


def nice_step(T):
    for s in (10, 15, 20, 30, 60, 120):
        if T / s <= 9:
            return s
    return 300


SHORT = {
    0: "Every motion blocks the model; every image and pose check is its own turn.",
    1: "Check a whole list of candidate poses in one call.",
    2: "All four cameras in one tiled image per look.",
    3: "A program's pictures come back in the same tool call.",
    4: "Action results arrive as messages: no polling turns.",
    5: "Actions run in the background while the model plans the next.",
    6: "Faster IK trims the planning calls (most was already hidden).",
}


def spd(x):
    return f"{x:.2f}x"


class Stages:
    def __init__(self, path):
        self.D = json.load(open(path))
        self.S = self.D["stages"]
        self.Tmax = max(s["wall_s"] for s in self.S) * 1.04

    # lanes geometry
    X0, X1 = 150, 1236
    YR = (232, 292)
    YA = (330, 376)

    def x(self, t):
        return self.X0 + (self.X1 - self.X0) * t / self.Tmax

    def bars(self, s, lane):
        out = []
        for b in sorted(s["lanes"].get(lane, []), key=lambda b: b["t0"]):
            st = b.get("state", "moving") if lane == "agent" else "moving"
            col = ROBOT_A if lane == "robot" else STATE_COL.get(st, MUTED)
            if col is None:
                continue
            out.append({"t0": b["t0"], "t1": b["t1"], "col": col, "label": b.get("label") or ""})
        if lane == "robot":                       # one bar per action: merge its commands
            merged = []
            for b in out:
                if merged and b["label"] == merged[-1]["label"] and b["t0"] - merged[-1]["t1"] < 0.6:
                    merged[-1]["t1"] = max(merged[-1]["t1"], b["t1"])
                else:
                    merged.append(dict(b))
            out = merged
        for i, b in enumerate(out):
            if lane == "robot":
                b["col"] = ROBOT_A if i % 2 == 0 else ROBOT_B
        return out

    def morph(self, A, B, k):
        """Bars between lists A and B at progress k: each B bar comes from a slice of an A bar."""
        nA, nB = len(A), len(B)
        res = []
        if nA == 0:
            for b in B:
                c = (b["t0"] + b["t1"]) / 2
                res.append((lerp(c, b["t0"], k), lerp(c, b["t1"], k), b["col"], k, b["label"]))
            return res
        groups = {}
        for j in range(nB):
            groups.setdefault(min(nA - 1, j * nA // max(1, nB)), []).append(j)
        for i, a in enumerate(A):
            js = groups.get(i)
            if not js:
                res.append((a["t0"], a["t1"], a["col"], 1 - k, ""))
                continue
            m = len(js)
            for q, j in enumerate(js):
                b = B[j]
                s0 = a["t0"] + (a["t1"] - a["t0"]) * q / m
                s1 = a["t0"] + (a["t1"] - a["t0"]) * (q + 1) / m
                res.append((lerp(s0, b["t0"], k), lerp(s1, b["t1"], k), lerpc(a["col"], b["col"], k), 1.0,
                            b["label"] if k > 0.5 else (a["label"] if m == 1 else "")))
        return res


def draw_stage_frame(S, i, k, labels_alpha=1.0):
    """Stage i morphing to stage i+1 at progress k (0: stage i)."""
    a = S.S[i]
    b = S.S[min(i + 1, len(S.S) - 1)]
    img = Image.new("RGBA", (W, H), BG)
    sc = 2
    lay = Image.new("RGBA", (W * sc, H * sc), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(lay)
    hdr = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(hdr, "RGBA")
    # header text: crossfade titles
    cur = a if k < 0.5 else b
    ta = 1 - abs(k - 0.5) * 2 if 0 < k < 1 else 1.0
    ta = 1.0 if k in (0.0, 1.0) else max(0.0, abs(k - 0.5) * 2)
    al = int(255 * ta)
    n = len(S.S)
    idx = (i if k < 0.5 else min(i + 1, n - 1)) + 1
    d.text((60, 44), f"WHERE THE TIME GOES  ·  STAGE {idx} OF {n}", font=F(13, "Bold"), fill=FAINT[:3] + (al,))
    d.text((60, 66), cur["title"], font=F(34, "Bold"), fill=TEXT[:3] + (al,))
    tw = d.textlength(cur["title"], font=F(34, "Bold"))
    kind = cur.get("kind", "modelled")
    kc = KIND_COL.get(kind, MUTED)
    bw = d.textlength(kind.upper(), font=F(12, "Bold")) + 24
    d.rounded_rectangle((60 + tw + 18, 80, 60 + tw + 18 + bw, 104), 12, fill=kc[:3] + (int(al * 0.95),))
    d.text((60 + tw + 18 + bw / 2, 92), kind.upper(), font=F(12, "Bold"), fill=hx("#0d1017")[:3] + (al,), anchor="mm")
    lines = R.wrap(d, SHORT.get(cur.get("id"), cur.get("one_line", "")), F(20), 1150)[:2]
    for q, ln in enumerate(lines):
        d.text((60, 124 + 26 * q), ln, font=F(20), fill=MUTED[:3] + (al,))
    ha = np.array(hdr)
    ha[..., 3] = (ha[..., 3].astype(np.float32) * ta).astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(ha))
    d = ImageDraw.Draw(img, "RGBA")
    # lanes panel
    d.rounded_rectangle((40, 196, W - 40, 440), 14, fill=PANEL)
    for (ya, yb) in (S.YR, S.YA):
        d.rounded_rectangle((S.X0, ya, S.X1, yb), 7, fill=TRACK)
    d.text((62, (S.YR[0] + S.YR[1]) / 2 - 7), "ROBOT", font=F(14, "Bold"), fill=TEXT, anchor="lm")
    d.text((62, (S.YR[0] + S.YR[1]) / 2 + 10), "moving / idle", font=F(10), fill=MUTED, anchor="lm")
    d.text((62, (S.YA[0] + S.YA[1]) / 2 - 7), "AGENT", font=F(14, "Bold"), fill=TEXT, anchor="lm")
    d.text((62, (S.YA[0] + S.YA[1]) / 2 + 10), "model / tools", font=F(10), fill=MUTED, anchor="lm")
    step = nice_step(S.Tmax)
    t = 0
    while t <= S.Tmax:
        x = S.x(t)
        d.line((x, S.YA[1] + 10, x, S.YA[1] + 14), fill=FAINT)
        d.text((x, S.YA[1] + 26), f"{t:.0f} s", font=F(10), fill=MUTED, anchor="mm")
        t += step
    ke = ease_io(k)
    fb = F(11 * sc, "Bold")
    for lane, (ya, yb) in (("robot", S.YR), ("agent", S.YA)):
        for (t0, t1, col, alpha, label) in S.morph(S.bars(a, lane), S.bars(b, lane), ke):
            x0, x1 = S.x(t0) * sc, S.x(t1) * sc
            if x1 - x0 < 1.5 * sc:
                c = (x0 + x1) / 2
                x0, x1 = c - 0.75 * sc, c + 0.75 * sc
            gap = sc if lane == "robot" and x1 - x0 > 4 * sc else 0
            r = min(6 * sc if lane == "robot" else 4 * sc, (x1 - x0 - 2 * gap) / 2)
            d2.rounded_rectangle((x0 + gap, ya * sc, x1 - gap, yb * sc), max(0, r), fill=col[:3] + (int(255 * alpha),))
            if lane == "robot" and label and alpha > 0.9 and labels_alpha > 0:
                avail = x1 - x0 - 10 * sc
                if avail > 30 * sc:
                    s = R.ellipsize(d2, label, fb, avail)
                    if s and s != "…":
                        d2.text(((x0 + x1) / 2, (ya + yb) * sc / 2), s, font=fb, fill=hx("#08201b")[:3] + (int(255 * labels_alpha),), anchor="mm")
    # wall end marker
    wall = lerp(a["wall_s"], b["wall_s"], ke)
    xw = S.x(wall) * sc
    for yy in range(int((S.YR[0] - 16) * sc), int((S.YA[1] + 6) * sc), 8 * sc):
        d2.line((xw, yy, xw, yy + 4 * sc), fill=TEXT[:3] + (200,), width=sc)
    lay = lay.resize((W, H), Image.LANCZOS)
    img = Image.alpha_composite(img, lay)
    d = ImageDraw.Draw(img, "RGBA")
    xw = S.x(wall)
    s = f"done at {wall:.0f} s"
    tw = d.textlength(s, font=F(12, "Bold"))
    xl = min(xw, S.X1 - tw / 2)
    d.text((xl, S.YR[0] - 22), s, font=F(12, "Bold"), fill=TEXT, anchor="mm")
    # readouts
    base = S.S[0]["wall_s"]
    wall_v = lerp(a["wall_s"], b["wall_s"], ke)
    tiles = [(f"{wall_v:.0f} s", "wall time", TEXT),
             (spd(base / wall_v), "faster than the vanilla loop", hx("#f6b93b")),
             (f"{lerp(a.get('robot_busy_pct_first_motion') or 0, b.get('robot_busy_pct_first_motion') or 0, ke):.0f}%",
              "robot busy (first motion to end)", ROBOT_B),
             (f"{lerp(a.get('model_hidden_s') or 0, b.get('model_hidden_s') or 0, ke):.0f} s",
              "model time hidden behind motion", THINK)]
    tw_, gap = 276, 16
    x0 = (W - (4 * tw_ + 3 * gap)) / 2
    for q, (big, lab, col) in enumerate(tiles):
        x = x0 + q * (tw_ + gap)
        d.rounded_rectangle((x, 468, x + tw_, 580), 14, fill=PANEL)
        d.text((x + 20, 508), big, font=F(40, "Bold"), fill=col, anchor="lm")
        d.text((x + 20, 552), lab, font=F(14, "Bold"), fill=MUTED, anchor="lm")
    # legend
    items = [(ROBOT_A, "robot moving"), (THINK, "model: waiting / thinking"), (GEN, "model: generating"),
             (TOOL, "tool command"), (IMG, "images"), (REPORT, "report pushed")]
    f = F(12)
    ws = [20 + d.textlength(s_, font=f) + 26 for _, s_ in items]
    x = (W - sum(ws)) / 2
    for (col, s_), w_ in zip(items, ws):
        d.rounded_rectangle((x, 624, x + 13, 636), 3, fill=col)
        d.text((x + 20, 630), s_, font=f, fill=MUTED, anchor="lm")
        x += w_
    d.text((W / 2, 680), "The robot lane is idle wherever the agent makes it wait. Same time scale in every stage.",
           font=F(12), fill=FAINT, anchor="mm")
    return img.convert("RGB")


def comparison_frame(S, k):
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    d.text((60, 44), "ALL STAGES", font=F(13, "Bold"), fill=FAINT)
    d.text((60, 66), "Total time per stage, and speedup vs the vanilla loop", font=F(32, "Bold"), fill=TEXT)
    n = len(S.S)
    rowh = min(66, 460 // n)
    y0 = 140
    X0, X1 = 400, 1100
    Tm = max(s["wall_s"] for s in S.S)
    base = S.S[0]["wall_s"]
    for i, s in enumerate(S.S):
        y = y0 + i * rowh
        kk = ease(k * (1 + 0.12 * (n - 1)) - i * 0.12)
        d.text((60, y + rowh / 2 - 9), R.ellipsize(d, s["title"], F(16, "Bold"), 250), font=F(16, "Bold"), fill=TEXT, anchor="lm")
        kind = s.get("kind", "")
        kc = KIND_COL.get(kind, MUTED)
        d.text((60, y + rowh / 2 + 11), kind, font=F(11, "Bold"), fill=kc, anchor="lm")
        bh = rowh * 0.55
        yt = y + (rowh - bh) / 2
        d.rounded_rectangle((X0, yt, X1, yt + bh), 6, fill=TRACK)
        wall = s["wall_s"]
        mv = min(wall, s.get("robot_moving_s") or 0)
        xm = X0 + (X1 - X0) * mv / Tm * kk
        xw = X0 + (X1 - X0) * wall / Tm * kk
        if xw - X0 > 2:
            d.rounded_rectangle((X0, yt, xw, yt + bh), 6, fill=hx("#3a4254"))
        if xm - X0 > 2:
            d.rounded_rectangle((X0, yt, xm, yt + bh), 6, fill=ROBOT_A)
        if kk > 0.05:
            rel = f"   {spd(base / wall)} faster" if i else "   baseline"
            d.text((xw + 12, yt + bh / 2), f"{wall * kk:.0f} s{rel if kk > 0.99 else ''}", font=F(15, "Bold"), fill=TEXT, anchor="lm")
    yl = y0 + n * rowh + 12
    d.rounded_rectangle((X0, yl, X0 + 13, yl + 12), 3, fill=ROBOT_A)
    d.text((X0 + 20, yl + 6), "robot moving", font=F(12), fill=MUTED, anchor="lm")
    d.rounded_rectangle((X0 + 140, yl, X0 + 153, yl + 12), 3, fill=hx("#3a4254"))
    d.text((X0 + 160, yl + 6), "robot idle (waiting on the agent)", font=F(12), fill=MUTED, anchor="lm")
    # footnote
    fa = ease(k * 2 - 0.6)
    yf = yl + 30
    foot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(foot, "RGBA")
    d.text((60, yf), "Earlier stages are modelled from the measured cups-02 run (same work, same order); "
                     "Fast IK is projected. Assumptions: docs/demos/data/stages.json.",
           font=F(13), fill=MUTED[:3] + (int(255 * fa),))
    fa_ = np.array(foot)
    fa_[..., 3] = (fa_[..., 3].astype(np.float32) * fa).astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(fa_))
    return img.convert("RGB")


def card(lines, bg=None):
    img = bg.copy() if bg is not None else Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img, "RGBA")
    for (y, s, f, col) in lines:
        d.text((W / 2, y), s, font=f, fill=col, anchor="mm")
    return img.convert("RGB")


class Writer:
    def __init__(self, out):
        self.p = subprocess.Popen([R.FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                                   "-crf", "22", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
                                  stdin=subprocess.PIPE)
        self.n = 0
        self.last = None

    def put(self, img, times=1):
        b = img.tobytes()
        for _ in range(times):
            self.p.stdin.write(b)
        self.n += times
        self.last = img

    def fade_to(self, img, sec=0.5):
        a = self.last
        m = int(sec * FPS)
        for q in range(m):
            self.put(Image.blend(a, img, ease((q + 1) / m)))

    def close(self):
        self.p.stdin.close()
        self.p.wait()


def live_segment(wr, tag, speed, t_from, stills=None, still_at=None):
    run = R.Run(tag)
    run.speed = speed
    base = R.draw_base(run)
    lb, ld = R.draw_lanes(run), R.draw_lanes(run, dim=True)
    # measured badge in the header
    d = ImageDraw.Draw(base)
    s = "MEASURED"
    x = 22 + d.textlength(tag, font=F(17, "Bold")) + 12 + d.textlength(run.L["task"], font=F(15)) + 14
    d.rounded_rectangle((x, 14, x + 82, 34), 10, fill=ROBOT_B)
    d.text((x + 41, 24), s, font=F(11, "Bold"), fill=hx("#0d1017"), anchor="mm")
    first = R.compose(run, t_from, base, lb, ld).convert("RGB")
    wr.fade_to(first)
    n = int((run.T - t_from) / speed * FPS)
    for q in range(n + 1):
        t = t_from + q * speed / FPS
        img = R.compose(run, min(t, run.T), base, lb, ld).convert("RGB")
        wr.put(img)
        if stills and still_at and abs(t - still_at) < speed / FPS / 2 + 1e-6:
            img.save(os.path.join(stills, f"demo_{tag}.png"))
    return run


def main():
    stages_path, out = sys.argv[1], sys.argv[2]
    stills = sys.argv[sys.argv.index("--stills") + 1] if "--stills" in sys.argv else None
    S = Stages(stages_path)
    wr = Writer(out)
    # 1. title (short)
    cups = R.Run("cups-02")
    bg = R.blurred_bg(cups.cam(40)["front"].copy())
    title = card([(285, "REAL ROBOT  ·  LLM AGENT  ·  ACTION QUEUE", F(14, "Bold"), MUTED),
                  (340, "Hiding model time behind robot motion", F(46, "Bold"), TEXT),
                  (400, "An LLM agent drives two robot arms. Our harness lets it think while the robot moves.", F(19), MUTED)], bg)
    black = Image.new("RGB", (W, H), (13, 16, 23))
    wr.put(black, 1)
    wr.fade_to(title, 0.3)
    wr.put(title, int(1.5 * FPS))
    if stills:
        title.save(os.path.join(stills, "demo_title.png"))
    # 2. stages
    n = len(S.S)
    hold = 4.3
    wr.fade_to(draw_stage_frame(S, 0, 0.0), 0.4)
    for i in range(n):
        f0 = draw_stage_frame(S, i, 0.0)
        wr.put(f0, int(hold * FPS))
        if stills:
            f0.save(os.path.join(stills, f"demo_stage{i + 1}.png"))
        if i < n - 1:
            m = int(0.6 * FPS)
            for q in range(m):
                wr.put(draw_stage_frame(S, i, (q + 1) / m, labels_alpha=abs(1 - 2 * (q + 1) / m)))
    # comparison
    m = int(5.0 * FPS)
    c0 = comparison_frame(S, 0.0)
    wr.fade_to(c0, 0.4)
    for q in range(m):
        img = comparison_frame(S, min(1.0, q / (1.3 * FPS)))
        wr.put(img)
    if stills:
        img.save(os.path.join(stills, "demo_compare.png"))
    # 3. cups-02 live, fast
    T = cups.L["totals"]
    intro = card([(310, "THE REAL THING", F(14, "Bold"), MUTED),
                  (360, "cups-02, measured  ·  10× speed", F(36, "Bold"), TEXT)])
    wr.fade_to(intro, 0.3)
    wr.put(intro, int(0.9 * FPS))
    live_segment(wr, "cups-02", 10.0, 20.0, stills, 120.0)
    # closing
    by = {s_.get("id"): s_ for s_ in S.S}
    van, rep_, que = by[0], by[4], by[5]
    lines = [(200, "CUPS-02, SAME WORK", F(14, "Bold"), MUTED),
             (262, f"{van['wall_s'] / que['wall_s']:.1f}x faster than a vanilla agent loop", F(44, "Bold"), hx("#f6b93b")),
             (322, f"{rep_['wall_s'] / que['wall_s']:.1f}x from the queue alone", F(26, "Bold"), ROBOT_B),
             (372, f"robot busy from {van['robot_busy_pct_first_motion']:.0f}% to {que['robot_busy_pct_first_motion']:.0f}% of the time"
                   f"  ·  {T['overlap_busy_moving_s']:.0f} s of agent time hidden behind motion", F(18), TEXT),
             (440, "GPT-6 Astra · Codex 0.165 · effort medium · bimanual YAM cell · 2026-11-10", F(13), FAINT)]
    close = card(lines, R.blurred_bg(cups.cam(cups.T)["front"].copy()))
    wr.fade_to(close, 0.4)
    wr.put(close, int(2.8 * FPS))
    if stills:
        close.save(os.path.join(stills, "demo_closing.png"))
    wr.fade_to(black, 0.4)
    wr.close()
    print("wrote", out, wr.n / FPS, "s", os.path.getsize(out) / 1e6, "MB")


def fmt(t):
    return R.fmt_t(t)


if __name__ == "__main__":
    main()

"""Render a timeline demo video for a real-cell run from its lanes JSON and the run's cameras.

    python render.py RUN [--still T_SECONDS OUT.png]

RUN is cups-02, towel-fold-18 or towel-fold-23. Writes OUT/<run>-timeline-<speed>x.mp4. A --still at T = -1 is the
title card, T = -2 the summary card. Inputs default to ../../assets; override with the environment variables below.
"""
import bisect, csv, json, os, subprocess, sys, textwrap
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

if not features.check("raqm"):   # the published videos were laid out with raqm (kerning); without it text comes out wider
    print("warning: Pillow has no raqm; install FriBiDi (brew install fribidi / apt install libfribidi0) and on macOS run\n"
          "  with DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib (make.sh sets it)", file=sys.stderr)

ASSETS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
RUNS = os.environ.get("RUNS", os.path.join(ASSETS, "cameras"))          # <run>/frames.csv and front, left_wrist, right_wrist .mp4
DATA = os.environ.get("DATA", os.path.join(ASSETS, "timeline-clips"))   # <run>-lanes.json, code reading cut (trim_lanes.py)
DEMOS = os.environ.get("OUT", os.getcwd())                              # where the video goes
FFMPEG = os.environ.get("FFMPEG", "ffmpeg")
NOTO = os.path.join(ASSETS, "fonts") + os.sep

W, H = 1280, 720
_fc = {}


def F(size, w="Regular"):
    k = (size, w)
    if k not in _fc:
        name = {"Regular": "NotoSans-Regular.ttf", "Bold": "NotoSans-Bold.ttf", "Mono": "NotoSansMono-Regular.ttf",
                "MonoBold": "NotoSansMono-Bold.ttf", "Italic": "NotoSans-Italic.ttf"}[w]
        _fc[k] = ImageFont.truetype(NOTO + name, size)
    return _fc[k]


def hx(c, a=255):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


BG = hx("#0d1017")
PANEL = hx("#151a23")
TRACK = hx("#1e2430")
GRID = hx("#252c3a")
TEXT = hx("#e8ebf2")
MUTED = hx("#8a93a6")
FAINT = hx("#5d6678")
ROBOT_A = hx("#2bb39b")
ROBOT_B = hx("#47c9b1")
FAIL = hx("#ef5b5b")
THINK = hx("#9a86ff")
TOOL = hx("#f6b93b")
REPORT = hx("#5fd0ff")
LOOK = hx("#c9d3e3")
QUEUE = hx("#4f8cff")

# layout
CAM = (20, 50, 576, 432)               # x, y, w, h
RP = (612, 50, 648, 432)               # right panel
WR = [(628, 292, 224, 168), (864, 292, 224, 168)]
TILES = (1100, 292, 148, 168)
LP = (12, 494, 1256, 214)              # lanes panel
PX0, PX1 = 128, 1244
Y_CALL = 500
Y_ROBOT = (518, 560)
Y_REP = 566
Y_AGENT = (574, 600)
Y_QUEUE = (608, 630)
Y_AXIS = 636
Y_LEG = 676


def fmt_t(t, tenths=False):
    t = max(0.0, t)
    m, s = divmod(t, 60)
    return f"{int(m)}:{s:04.1f}" if tenths else f"{int(m)}:{int(s):02d}"


def text_w(d, s, f):
    return d.textlength(s, font=f)


def ellipsize(d, s, f, maxw):
    if text_w(d, s, f) <= maxw:
        return s
    while s and text_w(d, s + "…", f) > maxw:
        s = s[:-1]
    return s + "…" if s else ""


def union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        elif b > a:
            out.append([a, b])
    return out


def inter(A, B):
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        a, b = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if b > a:
            out.append([a, b])
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


class Cum:
    """Cumulative measure of a union of intervals up to t."""

    def __init__(self, iv):
        self.iv = iv
        self.a = [x for x, _ in iv]
        self.cum = [0.0]
        for x, y in iv:
            self.cum.append(self.cum[-1] + y - x)

    def __call__(self, t):
        k = bisect.bisect_right(self.a, t)
        if k == 0:
            return 0.0
        x, y = self.iv[k - 1]
        return self.cum[k - 1] + min(t, y) - x


class Run:
    def __init__(self, tag):
        self.tag = tag
        self.L = json.load(open(os.path.join(DATA, f"{tag}-lanes.json")))
        L = self.L
        self.T = L["t_end"]
        self.speed = L["video_speed"]
        self.w0 = L["wall0_unix"]
        self.actions = L["robot_actions"]
        self.agent = [a for a in L["agent"] if a["state"] != "idle"]
        self.agent_t0 = [a["t0"] for a in self.agent]
        self.reports = L["reports"]
        self.rep_t = [r["t"] for r in self.reports]
        self.depth = L["queue_depth"]
        self.depth_t = [d[0] for d in self.depth]
        self.msgs = L["messages"]
        self.msg_t = [m["t"] for m in self.msgs]
        move = union([[a["t0"], a["t1"]] for a in self.actions])
        busy = union([[a["t0"], a["t1"]] for a in self.agent])
        self.c_move = Cum(move)
        self.c_hidden = Cum(inter(move, busy))
        self.act_t0 = [a["t0"] for a in self.actions]
        run = os.path.join(RUNS, tag)
        self.fwall = [float(r["wall_s"]) for r in csv.DictReader(open(os.path.join(run, "frames.csv")))]
        self.caps = {c: cv2.VideoCapture(os.path.join(run, f"{c}.mp4")) for c in ("front", "left_wrist", "right_wrist")}
        self.fidx = -1
        self.frames = {}

    def x(self, t):
        return PX0 + (PX1 - PX0) * t / self.T

    # --- state queries
    def action_at(self, t):
        k = bisect.bisect_right(self.act_t0, t) - 1
        if k >= 0 and self.actions[k]["t0"] <= t < self.actions[k]["t1"]:
            return self.actions[k]
        return None

    def agent_at(self, t):
        k = bisect.bisect_right(self.agent_t0, t) - 1
        # tools sit inside thinking gaps; prefer a tool if one covers t
        for j in range(max(0, k - 2), min(len(self.agent), k + 2)):
            a = self.agent[j]
            if a["state"] == "tool" and a["t0"] <= t < a["t1"]:
                return a
        for j in range(max(0, k - 2), min(len(self.agent), k + 2)):
            a = self.agent[j]
            if a["t0"] <= t < a["t1"]:
                return a
        return None

    def depth_at(self, t):
        k = bisect.bisect_right(self.depth_t, t) - 1
        return self.depth[k][1] if k >= 0 else 0

    def last_report(self, t):
        k = bisect.bisect_right(self.rep_t, t) - 1
        return self.reports[k] if k >= 0 else None

    def last_msg(self, t):
        k = bisect.bisect_right(self.msg_t, t) - 1
        return self.msgs[k] if k >= 0 else None

    def cam(self, t):
        wall = self.w0 + t
        k = max(0, bisect.bisect_right(self.fwall, wall) - 1)
        while self.fidx < k:
            for c, cap in self.caps.items():
                ok, fr = cap.read()
                if ok:
                    self.frames[c] = fr
            self.fidx += 1
        return self.frames


def rounded_mask(w, h, r, scale=3):
    m = Image.new("L", (w * scale, h * scale), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * scale - 1, h * scale - 1), r * scale, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def paste_cv(img, fr, box, r=10, label=None):
    x, y, w, h = box
    if fr is None:
        return
    im = Image.fromarray(cv2.cvtColor(cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB))
    img.paste(im, (x, y), rounded_mask(w, h, r))
    if label:
        d = ImageDraw.Draw(img, "RGBA")
        f = F(11, "Bold")
        tw = text_w(d, label, f)
        d.rounded_rectangle((x + 8, y + 8, x + 8 + tw + 14, y + 8 + 20), 10, fill=(10, 12, 18, 180))
        d.text((x + 15, y + 10), label, font=f, fill=TEXT)


# ---------------------------------------------------------------- static layers
def draw_lanes(run, scale=2, dim=False):
    """The lanes' data marks as an RGBA image (full frame size), supersampled."""
    S = scale
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    X = lambda t: run.x(t) * S
    # robot actions
    fb = F(11 * S, "Bold")
    for i, a in enumerate(run.actions):
        x0, x1 = X(a["t0"]), max(X(a["t1"]), X(a["t0"]) + 3 * S)
        col = FAIL if not a["ok"] else (ROBOT_A if i % 2 == 0 else ROBOT_B)
        d.rounded_rectangle((x0 + S, Y_ROBOT[0] * S, x1 - S, Y_ROBOT[1] * S), min(6 * S, (x1 - x0) / 2 - S), fill=col)
        name = a["name"]
        avail = x1 - x0 - 10 * S
        if avail > 26 * S:
            s = ellipsize(d, name, fb, avail)
            if s and s != "…":
                tw = text_w(d, s, fb)
                cy = (Y_ROBOT[0] + Y_ROBOT[1]) * S / 2
                d.text(((x0 + x1) / 2 - tw / 2, cy), s, font=fb, fill=hx("#08201b"), anchor="lm")
    # agent: thinking first, then tools on top (min width so short calls show)
    for a in run.agent:
        if a["state"] != "thinking":
            continue
        x0, x1 = X(a["t0"]), X(a["t1"])
        if x1 - x0 < 0.5:
            continue
        d.rounded_rectangle((x0, Y_AGENT[0] * S, x1, Y_AGENT[1] * S), min(4 * S, (x1 - x0) / 2), fill=THINK)
    for a in run.agent:
        if a["state"] != "tool":
            continue
        x0, x1 = X(a["t0"]), X(a["t1"])
        if x1 - x0 < 2 * S:
            c = (x0 + x1) / 2
            x0, x1 = c - S, c + S
        d.rounded_rectangle((x0, Y_AGENT[0] * S, x1, Y_AGENT[1] * S), min(3 * S, (x1 - x0) / 2), fill=TOOL)
    # reports: small down triangles above the agent lane
    for r in run.reports:
        x = X(r["t"])
        col = FAIL if r["kind"] == "error" else (LOOK if r["kind"] == "look" else REPORT)
        y = Y_REP * S
        d.polygon([(x - 4 * S, y - 3 * S), (x + 4 * S, y - 3 * S), (x, y + 4 * S)], fill=col)
    # queue depth step area
    qmax = max(3, max(n for _, n in run.depth))
    y0, y1 = Y_QUEUE[1] * S, Y_QUEUE[0] * S
    pts = [(X(0), y0)]
    for k, (t, n) in enumerate(run.depth):
        yy = y0 - (y0 - y1) * n / qmax
        if k:
            pts.append((X(t), pts[-1][1]))
        pts.append((X(t), yy))
    pts.append((X(run.T), pts[-1][1]))
    pts.append((X(run.T), y0))
    d.polygon(pts, fill=QUEUE[:3] + (200,))
    d.line(pts[1:-1], fill=hx("#86b0ff"), width=S)
    img = img.resize((W, H), Image.LANCZOS)
    if dim:
        a = np.array(img).astype(np.float32)
        a[..., 3] *= 0.38
        img = Image.fromarray(a.astype(np.uint8))
    return img


def draw_base(run):
    img = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(img)
    L = run.L
    # header
    d.text((22, 13), run.tag, font=F(17, "Bold"), fill=TEXT)
    tw = text_w(d, run.tag, F(17, "Bold"))
    d.text((22 + tw + 12, 15), L["task"], font=F(15), fill=MUTED)
    right = f"GPT-6 Astra · Codex · effort {L['reasoning_effort']} · real robot"
    d.text((W - 22 - text_w(d, right, F(13)), 17), right, font=F(13), fill=FAINT)
    # panels
    d.rounded_rectangle((RP[0], RP[1], RP[0] + RP[2], RP[1] + RP[3]), 12, fill=PANEL)
    d.rounded_rectangle((LP[0], LP[1], LP[0] + LP[2], LP[1] + LP[3]), 12, fill=PANEL)
    # lane tracks
    for (ya, yb) in (Y_ROBOT, Y_AGENT, Y_QUEUE):
        d.rounded_rectangle((PX0, ya, PX1, yb), 6, fill=TRACK)
    # lane labels
    def lab(y, a, b):
        d.text((28, y), a, font=F(13, "Bold"), fill=TEXT, anchor="lm")
        d.text((28, y + 15), b, font=F(10), fill=MUTED, anchor="lm")
    lab((Y_ROBOT[0] + Y_ROBOT[1]) / 2 - 6, "ROBOT", "queue actions")
    lab((Y_AGENT[0] + Y_AGENT[1]) / 2 - 6, "AGENT", "model / tools")
    d.text((28, (Y_QUEUE[0] + Y_QUEUE[1]) / 2), "QUEUE", font=F(11, "Bold"), fill=TEXT, anchor="lm")
    d.text((76, (Y_QUEUE[0] + Y_QUEUE[1]) / 2), "waiting", font=F(10), fill=MUTED, anchor="lm")
    qmax = max(3, max(n for _, n in run.depth))
    # axis
    step = 30 if run.T <= 320 else 60
    t = 0
    while t <= run.T + 0.01:
        x = run.x(t)
        d.line((x, Y_AXIS - 3, x, Y_AXIS + 1), fill=FAINT, width=1)
        s = fmt_t(t)
        d.text((x, Y_AXIS + 9), s, font=F(10), fill=MUTED, anchor="mm")
        t += step
    # legend
    items = [("box", ROBOT_A, "robot action (moving)"), ("box", FAIL, "action refused"),
             ("box", THINK, "model thinking (waiting + generating)"), ("box", TOOL, "tool command"),
             ("tri", REPORT, "report pushed"), ("tri", LOOK, "look"), ("box", QUEUE, "actions waiting")]
    f = F(11)
    widths = [18 + text_w(d, s, f) + 22 for _, _, s in items]
    x = (W - sum(widths)) / 2
    for (kind, col, s), w in zip(items, widths):
        if kind == "box":
            d.rounded_rectangle((x, Y_LEG - 5, x + 12, Y_LEG + 5), 3, fill=col)
        else:
            d.polygon([(x + 1, Y_LEG - 4), (x + 11, Y_LEG - 4), (x + 6, Y_LEG + 5)], fill=col)
        d.text((x + 18, Y_LEG), s, font=f, fill=MUTED, anchor="lm")
        x += w
    # right panel static labels
    d.text((RP[0] + 18, RP[1] + 16), "ELAPSED", font=F(10, "Bold"), fill=FAINT)
    return img


# ---------------------------------------------------------------- frames
def compose(run, t, base, lanes_b, lanes_d):
    img = base.copy()
    frs = run.cam(t)
    paste_cv(img, frs.get("front"), CAM, 12, "front camera")
    paste_cv(img, frs.get("left_wrist"), WR[0], 8, "left wrist")
    paste_cv(img, frs.get("right_wrist"), WR[1], 8, "right wrist")
    # lanes: bright up to the playhead, dim after
    px = int(round(run.x(min(t, run.T))))
    a = np.array(img)
    lb = np.array(lanes_b)
    ld = np.array(lanes_d)
    y0, y1 = LP[1], LP[1] + LP[3]
    lay = np.concatenate([lb[y0:y1, :px], ld[y0:y1, px:]], axis=1).astype(np.float32)
    al = lay[..., 3:4] / 255.0
    a[y0:y1, :, :3] = (a[y0:y1, :, :3] * (1 - al) + lay[..., :3] * al).astype(np.uint8)
    img = Image.fromarray(a)
    d = ImageDraw.Draw(img, "RGBA")

    act = run.action_at(t)
    ag = run.agent_at(t)
    depth = run.depth_at(t)
    rep = run.last_report(t)

    # playhead
    d.line((px, Y_ROBOT[0] - 4, px, Y_QUEUE[1] + 3), fill=(255, 255, 255, 235), width=2)
    d.ellipse((px - 4, Y_QUEUE[1] + 1, px + 4, Y_QUEUE[1] + 9), fill=(255, 255, 255, 235))
    # callout with the live action name
    if act:
        s = act["name"]
        f = F(11, "Bold")
        tw = text_w(d, s, f)
        cx = min(max(px, PX0 + tw / 2 + 8), PX1 - tw / 2 - 8)
        col = FAIL if not act["ok"] else ROBOT_B
        d.rounded_rectangle((cx - tw / 2 - 8, Y_CALL - 4, cx + tw / 2 + 8, Y_CALL + 12), 8, fill=col)
        d.text((cx, Y_CALL + 4), s, font=f, fill=hx("#08201b"), anchor="mm")

    # right panel
    x0, y = RP[0] + 18, RP[1]
    d.text((x0, y + 30), fmt_t(t, True), font=F(38, "MonoBold"), fill=TEXT)
    sub = f"of {fmt_t(run.T)}"
    d.text((x0 + 170, y + 52), sub, font=F(14), fill=MUTED)
    badge = f"{run.speed:g}× speed"
    bw = text_w(d, badge, F(13, "Bold"))
    bx = RP[0] + RP[2] - 18 - bw - 20
    d.rounded_rectangle((bx, y + 22, bx + bw + 20, y + 46), 12, fill=hx("#232a38"))
    d.text((bx + 10, y + 34), badge, font=F(13, "Bold"), fill=TEXT, anchor="lm")

    def row(yy, dot, label, value, vcol, right=None):
        d.ellipse((x0, yy + 5, x0 + 10, yy + 15), fill=dot)
        d.text((x0 + 18, yy + 10), label, font=F(11, "Bold"), fill=FAINT, anchor="lm")
        maxw = RP[2] - 36 - 92 - (130 if right else 0)
        d.text((x0 + 92, yy + 10), ellipsize(d, value, F(18, "Bold"), maxw), font=F(18, "Bold"), fill=vcol, anchor="lm")
        if right:
            rw = text_w(d, right, F(13))
            d.text((RP[0] + RP[2] - 18 - rw, yy + 10), right, font=F(13), fill=MUTED, anchor="lm")

    qtxt = "queue empty" if depth == 0 else f"{depth} waiting in queue"
    if act:
        row(y + 104, ROBOT_B if act["ok"] else FAIL, "ROBOT", act["name"], ROBOT_B if act["ok"] else FAIL, qtxt)
    else:
        row(y + 104, FAINT, "ROBOT", "idle (holding)", MUTED, qtxt)
    if ag is None:
        row(y + 142, FAINT, "AGENT", "idle (between turns)", MUTED)
    elif ag["state"] == "tool":
        row(y + 142, TOOL, "AGENT", f"tool: {ag['kind']}", TOOL)
    else:
        row(y + 142, THINK, "AGENT", "thinking (model)", THINK)
    # last report
    yy = y + 180
    d.ellipse((x0, yy + 5, x0 + 10, yy + 15), fill=REPORT)
    d.text((x0 + 18, yy + 10), "REPORT", font=F(11, "Bold"), fill=FAINT, anchor="lm")
    if rep:
        age = t - rep["t"]
        s = rep["text"].replace("(the arms were holding)", "").strip()
        f = F(14)
        maxw = RP[2] - 36 - 92
        s = ellipsize(d, s, f, maxw - 16)
        tw = text_w(d, s, f)
        if age < 2.5:
            k = 1 - age / 2.5
            col = FAIL if rep["kind"] == "error" else REPORT
            d.rounded_rectangle((x0 + 84, yy - 1, x0 + 84 + tw + 16, yy + 21), 8, fill=col[:3] + (int(70 * k + 20),))
        d.text((x0 + 92, yy + 10), s, font=f, fill=TEXT if age < 2.5 else MUTED, anchor="lm")
    else:
        d.text((x0 + 92, yy + 10), "none yet", font=F(14), fill=FAINT, anchor="lm")
    # divider
    d.line((x0, y + 222, RP[0] + RP[2] - 18, y + 222), fill=GRID, width=1)
    # tiles
    tx, ty, tw_, th = TILES
    mv = run.c_move(min(t, run.T))
    pct = 100 * mv / t if t > 1 else 0.0
    hid = run.c_hidden(min(t, run.T))
    for k, (big, small1, small2, col) in enumerate([
            (f"{pct:.0f}%", "robot moving", f"{mv:.0f} s of {t:.0f} s", ROBOT_B),
            (f"{hid:.0f} s", "model time hidden", "behind motion", THINK)]):
        yy = ty + k * (th // 2 + 2)
        d.rounded_rectangle((tx, yy, tx + tw_, yy + th // 2 - 4), 10, fill=hx("#1c2230"))
        d.text((tx + 12, yy + 24), big, font=F(26, "Bold"), fill=col, anchor="lm")
        d.text((tx + 12, yy + 50), small1, font=F(11, "Bold"), fill=TEXT, anchor="lm")
        d.text((tx + 12, yy + 65), small2, font=F(10), fill=MUTED, anchor="lm")
    # agent message subtitle on the front camera
    m = run.last_msg(t)
    if m and t - m["t"] < 9.0:
        age = t - m["t"]
        alpha = 1.0 if age < 8.0 else (9.0 - age)
        f = F(14)
        words = " ".join(m["text"].split())
        lines = []
        cur = ""
        for w_ in words.split(" "):
            if text_w(d, cur + " " + w_, f) > CAM[2] - 40:
                lines.append(cur.strip())
                cur = w_
            else:
                cur += " " + w_
        lines.append(cur.strip())
        if len(lines) > 3:
            lines = lines[:3]
            lines[-1] = ellipsize(d, lines[-1] + " …", f, CAM[2] - 40)
        bh = 24 + 20 * len(lines)
        bx0, by1 = CAM[0] + 10, CAM[1] + CAM[3] - 10
        d.rounded_rectangle((bx0, by1 - bh, CAM[0] + CAM[2] - 10, by1), 10, fill=(8, 10, 16, int(195 * alpha)))
        d.text((bx0 + 10, by1 - bh + 6), "AGENT SAYS", font=F(9, "Bold"), fill=THINK[:3] + (int(255 * alpha),))
        for i, ln in enumerate(lines):
            d.text((bx0 + 10, by1 - bh + 20 + 20 * i), ln, font=f, fill=TEXT[:3] + (int(255 * alpha),))
    return img


def blurred_bg(fr):
    im = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((W, int(W * 0.75)), Image.LANCZOS)
    im = im.crop((0, (im.size[1] - H) // 2, W, (im.size[1] - H) // 2 + H)).filter(ImageFilter.GaussianBlur(18))
    a = np.array(im).astype(np.float32) * 0.28 + np.array(BG[:3], np.float32) * 0.55
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


def wrap(d, s, f, maxw):
    lines, cur = [], ""
    for w_ in s.split():
        if cur and text_w(d, cur + " " + w_, f) > maxw:
            lines.append(cur)
            cur = w_
        else:
            cur = (cur + " " + w_).strip()
    if cur:
        lines.append(cur)
    return lines


def title_card(run, fr):
    img = blurred_bg(fr)
    d = ImageDraw.Draw(img, "RGBA")
    L = run.L
    cy = 200
    s = f"REAL-ROBOT AGENT RUN  ·  {run.tag}"
    d.text((W / 2, cy), s, font=F(14, "Bold"), fill=MUTED, anchor="mm")
    d.text((W / 2, cy + 50), L["task"], font=F(40, "Bold"), fill=TEXT, anchor="mm")
    instr = L["instruction"].split("\n")[0]
    sents = instr.replace("r.finish()", "r.finish()").split(". ")
    short = ". ".join(sents[:3]).strip()
    if not short.endswith("."):
        short += "."
    lines = wrap(d, short, F(17), 860)[:3]
    for i, ln in enumerate(lines):
        d.text((W / 2, cy + 110 + 26 * i), ln, font=F(17), fill=MUTED, anchor="mm")
    by = cy + 110 + 26 * len(lines) + 40
    badges = [(f"{L['model'].replace('gpt-6-astra', 'GPT-6 Astra')} · Codex · effort {L['reasoning_effort']}", hx("#232a38"), TEXT),
              ("bimanual YAM cell, queued actions", hx("#232a38"), TEXT),
              (f"{run.speed:g}× speed", THINK, hx("#0d1017"))]
    f = F(15, "Bold")
    ws = [text_w(d, b, f) + 32 for b, _, _ in badges]
    x = W / 2 - (sum(ws) + 12 * (len(ws) - 1)) / 2
    for (b, bg, fg), w_ in zip(badges, ws):
        d.rounded_rectangle((x, by, x + w_, by + 34), 17, fill=bg)
        d.text((x + w_ / 2, by + 17), b, font=f, fill=fg, anchor="mm")
        x += w_ + 12
    return img.convert("RGB")


def summary_card(run, fr, lanes_b, base):
    img = blurred_bg(fr)
    d = ImageDraw.Draw(img, "RGBA")
    T = run.L["totals"]
    d.text((W / 2, 70), f"SUMMARY  ·  {run.tag}", font=F(14, "Bold"), fill=MUTED, anchor="mm")
    d.text((W / 2, 110), run.L["task"], font=F(28, "Bold"), fill=TEXT, anchor="mm")
    tiles = [
        (fmt_t(T["wall_s"]), "agent wall time", f"r.finish at {fmt_t(T['finish_t'])}", TEXT),
        (f"{T['robot_moving_s']:.0f} s", "robot moving", f"{T['robot_moving_pct']:.0f}% of wall, {T['robot_moving_pct_first_motion_to_finish']:.0f}% from first motion", ROBOT_B),
        (f"{T['model_thinking_s']:.0f} s", "model thinking", f"{T['tool_s']:.0f} s more in tool commands", THINK),
        (f"{T['overlap_busy_moving_s']:.0f} s", "agent time hidden", "behind robot motion", THINK),
        (f"{T['robot_idle_while_agent_busy_s']:.0f} s", "robot waiting", "on the agent", MUTED),
        (str(T["actions"]), "queued actions", f"{T['actions_failed']} refused" if T["actions_failed"] else "none refused", ROBOT_B),
        (str(T["queue_max_depth"]), "max queue depth", "actions waiting at once", QUEUE),
        (str(T["tool_calls"]), "tool calls", f"{T['reports']} pushed reports", TOOL),
    ]
    cols, tw_, th, gap = 4, 270, 112, 16
    x0 = (W - (cols * tw_ + (cols - 1) * gap)) / 2
    for i, (big, l1, l2, col) in enumerate(tiles):
        x = x0 + (i % cols) * (tw_ + gap)
        y = 160 + (i // cols) * (th + gap)
        d.rounded_rectangle((x, y, x + tw_, y + th), 14, fill=(21, 26, 35, 235))
        d.text((x + 18, y + 34), big, font=F(34, "Bold"), fill=col, anchor="lm")
        d.text((x + 18, y + 72), l1, font=F(14, "Bold"), fill=TEXT, anchor="lm")
        d.text((x + 18, y + 92), ellipsize(d, l2, F(12), tw_ - 30), font=F(12), fill=MUTED, anchor="lm")
    # the full lanes, bright
    lane_area = base.crop((0, LP[1], W, LP[1] + LP[3]))
    la = Image.alpha_composite(lane_area, lanes_b.crop((0, LP[1], W, LP[1] + LP[3])))
    img.paste(la, (0, H - LP[3] - 6))
    return img.convert("RGB")


def blend(a, b, k):
    return Image.blend(a, b, k)


def main():
    tag = sys.argv[1]
    still = None
    if "--still" in sys.argv:
        i = sys.argv.index("--still")
        still = (float(sys.argv[i + 1]), sys.argv[i + 2])
    fps = 30
    run = Run(tag)
    base = draw_base(run)
    lanes_b = draw_lanes(run)
    lanes_d = draw_lanes(run, dim=True)
    if still:
        t, out = still
        if t < 0:
            fr = run.cam(0)["front"].copy()
            img = title_card(run, fr) if t == -1 else summary_card(run, run.cam(run.T)["front"].copy(), lanes_b, base)
        else:
            img = compose(run, t, base, lanes_b, lanes_d)
        img.convert("RGB").save(out)
        print("wrote", out)
        return
    out = os.path.join(DEMOS, f"{tag}-timeline-{run.speed:g}x.mp4")
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
           "-i", "-", "-c:v", "libx264", "-preset", "slow", "-crf", "23", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    first = run.cam(0)["front"].copy()
    tc = title_card(run, first)
    n_title, n_fade = int(2.6 * fps), int(0.5 * fps)
    first_main = compose(run, 0.0, base, lanes_b, lanes_d).convert("RGB")
    for i in range(n_title):
        p.stdin.write(tc.tobytes())
    for i in range(n_fade):
        p.stdin.write(blend(tc, first_main, (i + 1) / n_fade).tobytes())
    n_main = int(run.T / run.speed * fps)
    last = None
    for i in range(n_main + 1):
        t = min(run.T, i * run.speed / fps)
        img = compose(run, t, base, lanes_b, lanes_d).convert("RGB")
        p.stdin.write(img.tobytes())
        last = img
        if i % 300 == 0:
            print(f"{tag}: {i}/{n_main}", flush=True)
    sc = summary_card(run, run.frames["front"].copy(), lanes_b, base)
    for i in range(n_fade):
        p.stdin.write(blend(last, sc, (i + 1) / n_fade).tobytes())
    for i in range(int(5.0 * fps)):
        p.stdin.write(sc.tobytes())
    p.stdin.close()
    p.wait()
    print("wrote", out, os.path.getsize(out) / 1e6, "MB")


if __name__ == "__main__":
    main()

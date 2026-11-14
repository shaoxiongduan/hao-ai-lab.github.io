"""Write lanes JSON with the initial code-reading phase cut: every time shifted by -cut, intervals before it dropped
or clipped, camera sync moved (wall0 + cut), totals recomputed. Reads ../../assets/runs/data (robot-api's
docs/demos/data), writes ../../assets/timeline-clips. Usage: python trim_lanes.py cups-02 towel-fold-18 towel-fold-23"""
import json, sys
import os
ASSETS = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
SRC = os.environ.get("SRC", os.path.join(ASSETS, "runs", "data"))
DST = os.environ.get("DST", os.path.join(ASSETS, "timeline-clips"))
CUTS = json.load(open(os.path.join(ASSETS, "timeline-clips", "cuts.json")))   # per run: "cut" = seconds of code reading

def union(iv):
    out = []
    for a, b in sorted(iv):
        if out and a <= out[-1][1]: out[-1][1] = max(out[-1][1], b)
        else: out.append([a, b])
    return out

def inter_len(A, B):
    s = 0.0
    for a, b in A:
        for c, d in B:
            s += max(0.0, min(b, d) - max(a, c))
    return s

for tag in sys.argv[1:]:
    L = json.load(open(f"{SRC}/{tag}-lanes.json"))
    c = CUTS[tag]["cut"]
    sh = lambda t: round(t - c, 3)
    def iv(xs, k0="t0", k1="t1"):
        out = []
        for x in xs:
            if x[k1] <= c: continue
            y = dict(x); y[k0] = sh(max(x[k0], c)); y[k1] = sh(x[k1])
            if "queued_t" in y: y["queued_t"] = sh(max(y["queued_t"], c))
            out.append(y)
        return out
    dropped_tools = sum(1 for a in L["agent"] if a["state"] == "tool" and a["t1"] <= c)
    L["agent"] = iv(L["agent"])
    L["robot_actions"] = iv(L["robot_actions"])
    L["turns"] = [[sh(max(a, c)), sh(b)] for a, b in L["turns"] if b > c]
    for k in ("reports", "messages"):
        L[k] = [dict(x, t=sh(x["t"])) for x in L[k] if x["t"] >= c]
    qd = [[sh(t), n] for t, n in L["queue_depth"] if t >= c]
    L["queue_depth"] = [[0.0, 0]] + [q for q in qd if q[0] > 0]
    L["wall0_unix"] += c
    L["t_end"] = sh(L["t_end"])
    L["trimmed_reading_s"] = c
    T = L["totals"]
    move = union([[a["t0"], a["t1"]] for a in L["robot_actions"]])
    think = union([[a["t0"], a["t1"]] for a in L["agent"] if a["state"] == "thinking"])
    tool = union([[a["t0"], a["t1"]] for a in L["agent"] if a["state"] == "tool"])
    busy = union(think + tool)
    msum = lambda U: sum(b - a for a, b in U)
    T.update(wall_s=round(T["wall_s"] - c, 1), finish_t=round(T["finish_t"] - c, 1),
             first_motion_t=round(T["first_motion_t"] - c, 1), robot_moving_s=round(msum(move), 1),
             model_thinking_s=round(msum(think), 1), tool_s=round(msum(tool), 1), agent_busy_s=round(msum(busy), 1),
             overlap_busy_moving_s=round(inter_len(busy, move), 1), overlap_thinking_moving_s=round(inter_len(think, move), 1),
             tool_calls=T["tool_calls"] - dropped_tools)
    T["robot_moving_pct"] = round(100 * T["robot_moving_s"] / T["wall_s"], 1)
    T["agent_idle_s"] = round(T["wall_s"] - T["agent_busy_s"], 1)
    T["robot_idle_while_agent_busy_s"] = round(T["agent_busy_s"] - T["overlap_busy_moving_s"], 1)
    json.dump(L, open(f"{DST}/{tag}-lanes.json", "w"), indent=1)
    print(tag, "cut", c, {k: T[k] for k in ("wall_s", "finish_t", "model_thinking_s", "overlap_busy_moving_s", "tool_calls")})

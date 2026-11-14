"""Compute robot / agent / queue lanes for a real-cell agent run (read-only) -> docs/demos/data/<run>-lanes.json."""
import glob, json, os, re, sys
from datetime import datetime

RUNS = "/home/shao/robot-api-real/agent-runs"
OUT = "/home/shao/robot-api-real/robot-api-dsk/docs/demos/data"

TASK_TITLE = {
    "cups-02": "Find the pear and hide it under the empty cup",
    "towel-fold-18": "Spread a partly folded towel, fold it in half",
    "towel-fold-23": "Smooth a crumpled towel, fold it in half",
}
SPEED = {"cups-02": 2.5, "towel-fold-18": 2.5, "towel-fold-23": 3.0}


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def union(iv):
    out = []
    for a, b in sorted(iv):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
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


def minus(A, B):
    out = []
    for a, b in A:
        cur = a
        for x, y in B:
            if y <= cur or x >= b:
                continue
            if x > cur:
                out.append([cur, x])
            cur = max(cur, y)
        if cur < b:
            out.append([cur, b])
    return out


def total(A):
    return sum(b - a for a, b in A)


def tool_kind(txt, name):
    if name in ("wait", "sleep"):
        return "waiting on a command"
    if re.search(r"\.queue\(|r\.run\(|\.then\(|queue\b", txt) and "def " in txt:
        return "queueing an action"
    if re.search(r"\.move\w*\(|\.gripper\(|move_at\(", txt):
        return "moving the robot"
    if re.search(r"view_image|capture\(|review\(|\.cameras\(|Overlay|View3D|viz\.|show_cameras|marks\(", txt):
        return "looking at cameras"
    if re.search(r"point\(|\.ik\(|reachable\(|dry_run", txt):
        return "checking reach / IK"
    if re.search(r"finish\(", txt):
        return "finishing"
    if re.search(r"\b(cat|sed|grep|rg|head|tail|ls|find|wc)\b", txt) and "robot.kernel" not in txt:
        return "reading files"
    return "running code"


def build(tag):
    run = os.path.join(RUNS, tag)
    meta = json.load(open(os.path.join(run, "meta.json")))
    tl = [json.loads(l) for l in open(os.path.join(run, "timeline.jsonl"))]
    w0 = tl[0]["wall"] - tl[0]["t"]
    rel = lambda w: round(w - w0, 3)
    ev = [json.loads(l) for l in open(os.path.join(run, "codex", "events.jsonl"))]

    # turns (agent active) from the app-server's events
    turns, cur = [], None
    for d in ev:
        if d["type"] == "turn.started":
            cur = d["wall"]
        elif d["type"] == "turn.completed" and cur is not None:
            turns.append([rel(cur), rel(d["wall"])])
            cur = None
    t_end = round(turns[-1][1] + 1.0, 3)
    finish_t = next((d["t"] for d in tl if d.get("kind") == "finish"), None)

    # tool calls: rollout call -> output
    calls = {}
    for p in sorted(glob.glob(os.path.join(run, "codex", "home", "sessions", "**", "rollout-*.jsonl"), recursive=True)):
        started = False
        for line in open(p, errors="replace"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            pl = e.get("payload") or {}
            typ = pl.get("type")
            if e.get("type") == "event_msg" and typ == "task_started":
                started = True
            if not started or e.get("type") != "response_item":
                continue
            if typ in ("custom_tool_call", "function_call"):
                cid = pl.get("call_id")
                if cid not in calls:
                    txt = pl.get("input") or pl.get("arguments") or ""
                    m = re.search(r'cmd\s*:\s*"((?:[^"\\]|\\.)*)"', txt)
                    calls[cid] = {"t0": rel(ts(e["timestamp"])), "name": pl.get("name"),
                                  "kind": tool_kind(txt, pl.get("name")),
                                  "cmd": (m.group(1)[:160] if m else txt[:160])}
            elif typ in ("custom_tool_call_output", "function_call_output"):
                c = calls.get(pl.get("call_id"))
                if c is not None and "t1" not in c:
                    c["t1"] = rel(ts(e["timestamp"]))
    tools = sorted([c for c in calls.values() if "t1" in c], key=lambda c: c["t0"])
    tool_iv = union([[c["t0"], c["t1"]] for c in tools])
    turn_iv = union(turns)
    think_iv = minus(turn_iv, tool_iv)
    idle_iv = minus([[0.0, t_end]], turn_iv)

    agent = []
    for a, b in think_iv:
        agent.append({"t0": round(a, 3), "t1": round(b, 3), "state": "thinking"})
    for c in tools:
        # clip into turn windows; merge overlapping calls by keeping each call (they do not overlap in practice)
        agent.append({"t0": c["t0"], "t1": c["t1"], "state": "tool", "kind": c["kind"], "tool": c["name"],
                      "cmd": c["cmd"]})
    for a, b in idle_iv:
        agent.append({"t0": round(a, 3), "t1": round(b, 3), "state": "idle"})
    agent.sort(key=lambda x: x["t0"])

    # pushed reports
    reports = []
    for d in ev:
        if d["type"] != "action.message":
            continue
        first = (d.get("text") or "").splitlines()[0]
        m = re.match(r"\[action (\S+)\] (.*)", first)
        if m:
            k = "started" if m.group(2).startswith("started") else ("done" if m.group(2).startswith("done") else "error")
            reports.append({"t": rel(d["wall"]), "kind": k, "action": m.group(1), "text": first[:200]})
        elif first.startswith("[look"):
            reports.append({"t": rel(d["wall"]), "kind": "look", "action": None, "text": first[:200]})
        else:
            reports.append({"t": rel(d["wall"]), "kind": "other", "action": None, "text": first[:200]})

    # queue
    q = [json.loads(l) for l in open(os.path.join(run, "workspace", ".robot", "events", "queue.jsonl"))]
    queued_at = {d["id"]: d["wall"] for d in q if d["event"] == "queued"}
    started_at = {d["id"]: d["wall"] for d in q if d["event"] == "started"}
    actions = []
    for d in q:
        if d["event"] == "ended":
            actions.append({"id": d["id"], "name": d["name"], "t0": rel(d["t0"]), "t1": rel(d["t1"]),
                            "ok": bool(d.get("ok")), "status": d.get("status"),
                            "queued_t": rel(queued_at[d["id"]]) if d["id"] in queued_at else rel(started_at.get(d["id"], d["t0"])),
                            "commands": d.get("commands")})
    depth = [[0.0, 0]]
    for d in q:
        if "waiting" in d:
            t = rel(d["wall"])
            n = len(d["waiting"])
            if depth[-1][0] == t:
                depth[-1][1] = n
            elif depth[-1][1] != n:
                depth.append([t, n])

    msgs = [{"t": d["t"], "text": d["text"].strip()} for d in tl
            if d["src"] == "agent" and d["kind"] == "message" and d.get("text", "").strip()]

    move_iv = union([[a["t0"], min(a["t1"], t_end)] for a in actions])
    busy_iv = union(tool_iv + think_iv)
    first_motion = move_iv[0][0] if move_iv else None
    span = (finish_t or t_end) - (first_motion or 0)
    totals = {
        "wall_s": round(t_end, 1),
        "finish_t": round(finish_t, 1) if finish_t else None,
        "robot_moving_s": round(total(move_iv), 1),
        "robot_moving_pct": round(100 * total(move_iv) / t_end, 1),
        "first_motion_t": round(first_motion, 1) if first_motion is not None else None,
        "robot_moving_pct_first_motion_to_finish": round(100 * total(inter(move_iv, [[first_motion, finish_t or t_end]])) / span, 1) if first_motion is not None else None,
        "model_thinking_s": round(total(think_iv), 1),
        "tool_s": round(total(tool_iv), 1),
        "agent_busy_s": round(total(busy_iv), 1),
        "agent_idle_s": round(total(idle_iv), 1),
        "overlap_busy_moving_s": round(total(inter(busy_iv, move_iv)), 1),
        "overlap_thinking_moving_s": round(total(inter(think_iv, move_iv)), 1),
        "robot_idle_while_agent_busy_s": round(total(minus(busy_iv, move_iv)), 1),
        "actions": len(actions),
        "actions_failed": sum(1 for a in actions if not a["ok"]),
        "queue_max_depth": max(n for _, n in depth),
        "tool_calls": len(tools),
        "reports": len(reports),
        "turns": len(turns),
        "threads": len(meta.get("codex_threads") or []),
    }
    cx = meta.get("codex") or {}
    out = {
        "schema": "robotapi.demo-lanes.v1",
        "run": tag,
        "task": TASK_TITLE.get(tag, meta.get("task")),
        "instruction": meta.get("instruction"),
        "model": cx.get("model"), "reasoning_effort": cx.get("reasoning_effort"),
        "service_tier": cx.get("service_tier"), "codex_version": cx.get("version"),
        "video_speed": SPEED.get(tag, 2.5),
        "wall0_unix": round(w0, 3),
        "t_end": t_end,
        "turns": turns,
        "robot_actions": actions,
        "agent": agent,
        "reports": reports,
        "queue_depth": depth,
        "messages": msgs,
        "totals": totals,
    }
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"{tag}-lanes.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(tag, json.dumps(totals))
    return out


if __name__ == "__main__":
    for t in sys.argv[1:]:
        build(t)

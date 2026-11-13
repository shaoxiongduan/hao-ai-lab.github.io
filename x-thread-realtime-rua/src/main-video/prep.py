"""Build data.json for comp2.html: the six stages (stages.json shifted by the 7.0 s code reading, as in the blog)
and the three real runs (lanes from <run>-lanes.json, clocks starting after the code reading)."""
import json, sys
dsk, out = sys.argv[1], sys.argv[2]
S = json.load(open(f"{dsk}/stages.json"))["stages"]
CUT = 7.0
CODE = {"thinking": "w", "generating": "g", "tool": "t", "images": "i", "report": "r"}
TITLE = {4: "+ Automatic look", 5: "+ Pipelining"}                       # stages.json still says "+ Pushed reports"
REQ = [164, 155, 107, 73, 59, 59]                     # blog Fig 11 (stages.json turns minus the 2 reading turns)
SUB = ["Every action blocks, and every image and check is its own model request.",
       "A whole list of candidate poses is checked in one call.",
       "All four cameras come back as one tiled image.",
       "A program's pictures come back in the same tool call.",
       "Each action ends with its result, state and camera grid: no turn to look.",
       "Actions run in the background while the model plans the next ones."]
stages = []
for st in S[:6]:
    L = st["lanes"]
    ag = [[round(max(a["t0"] - CUT, 0), 3), round(a["t1"] - CUT, 3), CODE[a["state"]], a["key"]] for a in L["agent"] if a["t1"] - CUT > 0]
    rb = [[round(r["t0"] - CUT, 3), round(r["t1"] - CUT, 3), r["key"]] for r in L["robot"]]
    stages.append({"id": st["id"], "title": TITLE.get(st["id"], st["title"]), "sub": SUB[st["id"]], "kind": st["kind"],
                   "wall": round(st["wall_s"] - CUT, 1), "moving": round(st["robot_busy_pct_first_motion"]),
                   "hidden": round(st["model_hidden_s"]), "req": REQ[st["id"]], "agent": ag, "robot": rb})
runs = []
for run, T, speed, name in [("cups-02", 204.4, 27, "Hide the pear under the empty cup"),
                            ("towel-fold-18", 143.0, 17, "Spread a partly folded towel, fold it in half"),
                            ("towel-fold-23", 484.0, 60, "The same, from a crumpled towel")]:
    L = json.load(open(f"{dsk}/{run}-lanes.json")); Tt = L["totals"]
    s0 = Tt["finish_t"] - T
    sh = lambda x: round(x - s0, 2)
    runs.append({"run": run, "name": name, "T": T, "speed": speed, "start": round(s0, 2),
                 "actions": Tt["actions"], "moving": round(Tt["robot_moving_pct_first_motion_to_finish"]),
                 "robot": [[sh(a["t0"]), sh(a["t1"]), 1 if a["ok"] else 0] for a in L["robot_actions"] if a["t1"] > s0],
                 "agent": [[sh(max(a["t0"], s0)), sh(a["t1"]), {"thinking": "w", "tool": "t"}[a["state"]]] for a in L["agent"] if a["t1"] > s0 and a["state"] != "idle" and a["t0"] < Tt["finish_t"]]})
json.dump({"stages": stages, "runs": runs}, open(out, "w"), separators=(",", ":"))
for s in stages: print(s["id"], s["title"], s["wall"], s["req"], s["moving"], s["hidden"], len(s["agent"]), len(s["robot"]))
for r in runs: print(r["run"], r["start"], r["T"], r["speed"], round(r["T"] / r["speed"], 2), r["actions"], r["moving"], len(r["robot"]), len(r["agent"]))

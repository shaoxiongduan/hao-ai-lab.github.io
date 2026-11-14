# Demo videos from the real cell

Front-camera recordings, at real speed (6 fps, 640x480, H.264), of three real-cell episodes on 2026-11-10. In each one GPT-6
Astra (Codex 0.165.0, effort medium, the ultrafast tier) worked through the queue (`agent_run_real.py --staggered`).
The full run folders, with every camera, the timeline and the queue journal, are on the cell PC under
`~/robot-api-real/agent-runs/<run>/`.

| Video | Task | `r.finish` / wall | What happens |
|---|---|---|---|
| `cups-02-front.mp4` | Three red cups: one hides a pear, one a ball, one nothing. Put the pear under the empty cup. | 211 s / 284 s | Lifts each cup in turn and finds the pear (right), the empty cup (middle) and the ball. Moves the pear to the middle and covers it with the empty cup. Eleven queued actions ran back to back, and the robot was moving 84% of the time from its first motion to `r.finish`. |
| `towel-fold-18-front.mp4` | A towel lying partly folded over: spread it flat and fold it once in half. | 151 s / 220 s | Grabs the two near corners, pulls back so the towel drags out flat, and folds it in half lengthwise with straight edges. 11 actions, one IK refusal it planned around. |
| `towel-fold-23-front.mp4` | The same, from a crumpled towel. | 503 s / 575 s | Smooths it out by pressing the fingertips on the cloth and dragging outward, scoops two corners and folds. The first fold comes out crinkled. It recovers on its own: it lifts the fold so the cloth hangs taut, then lays it back down. |

Cell settings for all three:
- the measured gravity factors (`YAM_GRAVITY_FACTORS=1.0,1.2,1.1,0.5,1.0,1.0`);
- the settle trim, with a deadband, a freeze on crossing and a reset on each move;
- the wrist cameras on their CAD mount (`YAM_CALIBRATION_IGNORE=wrist_camera_corrections`);
- for the towels, the cloth fence (`fence-cloth.json`).

The towel instructions are in the run folders' `meta.json`.

## Timeline videos, traces and lane data

- `<run>-timeline-<speed>x.mp4` (1280x720, H.264): the same episodes sped up (2.5x; towel-fold-23 3x), from the agent's
  start to just after `r.finish`. Top: the front camera and both wrist cameras, synced by wall time. Bottom: the ROBOT
  lane (each queued action while it ran, refusals in red), the AGENT lane (model thinking in violet: the request in
  flight, waiting plus generating; tool commands in amber; pushed reports as triangles), and the queue depth (actions
  waiting). The panel shows the live action, agent state, last report, the share of time the robot has been moving and
  the agent time hidden behind motion so far. Title and summary cards at the ends.
- `pipelining-demo.mp4`: a 66 s story: how the time is spent at each stage (animated lanes, `data/stages.json`; the
  stages before the queue are modelled from cups-02, Fast IK is projected), each stage's speedup over a vanilla agent
  loop, then cups-02 played at 10x with its live lanes.
- `traces/<run>/`: the Codex rollouts, the images the agent saw, the timeline and the queue journal (see
  `traces/README.md`).
- `data/<run>-lanes.json`: the intervals behind the videos (schema and derivation in `data/README.md`).
- `pipeline.html`: the same stage story as an interactive page (open it in a browser; arrow keys step through the
  stages, `#stage0`-`#stage6` deep-link). Stages before "The queue" are modelled from the measured cups-02 run, and
  the last is projected; the rules are on the page and in `data/stages.json`.

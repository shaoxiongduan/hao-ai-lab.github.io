# Agent traces from the demo runs

Codex session traces from the three real-cell episodes in `docs/demos/` (2026-11-10, `agent_run_real.py --staggered`).
GPT-6 Astra, effort medium, ultrafast tier, codex-cli 0.165.0. The format matches `robot-api-speed/traces/`, plus each
run's queue journal and machine-readable timeline.

| Run | Task | Agent wall (`r.finish`) | Model calls | Actions | Outcome |
|---|---|---|---|---|---|
| `cups-02/` | Three red cups: one hides a pear, one a ball, one nothing. Put the pear under the empty cup. | 272 s (211 s) | 60 | 14, none refused | Lifted each cup, found the pear (right), the empty cup (middle) and the ball; moved the pear to the middle, covered it; `r.finish`. Robot moving 84% of the time from first motion to `r.finish`; up to 3 actions waiting in the queue. |
| `towel-fold-18/` | A towel lying partly folded over: spread it flat, fold it once in half. | 212 s (151 s) | 44 | 11, one IK refusal | Grabbed the near corners, pulled it flat, folded it lengthwise; planned around the refused `fold_across` with `across_revised`; `r.finish`. |
| `towel-fold-23/` | The same, from a crumpled towel, with a smoothing-first plan. | 564 s (502 s) | 110 | 32, one separation refusal | Smoothed it by pressing and dragging, scooped two corners, folded; fixed the crinkled first fold by lifting it taut and laying it back down; `r.finish`. |

Each folder holds:

- `rollout-N.jsonl`: Codex's own record of the conversation, one file per thread in order. The harness moves the
  conversation to a fresh thread after about 20 images, and each new thread starts with the history carried over
  (items before the thread's `task_started` event are that carried history). Each line is one item: the agent's
  messages, its tool calls (`custom_tool_call` named `exec`: JavaScript that calls `tools.exec_command`, usually with a
  `python -m robot.kernel` heredoc; `function_call` named `wait` for a running command) and their outputs, the pushed
  reports (`[action ...]`, `[look N]`, `[queue] ...`) and token counts. Camera images are replaced by
  `<image omitted (N KB): see views/>`. Encrypted reasoning is omitted (it was opaque; reasoning summaries were off).
  The account ids in `session_meta` are blanked.
- `views/`: the images the agent made or was sent, as JPEGs at most 960 px (`after-NAME`: the camera grid as action
  NAME ended; `look-N`: a look while an action ran; the rest are its own review pictures, named as in its code). Where
  the agent reused a name, the last picture under it is kept.
- `TIMELINE.md`: the episode at a glance: every command, motion, report and message, with times from the start.
- `timeline.jsonl`: the same events as JSON, one per line, `t` in seconds from the start and `wall` (Unix time):
  `src: agent` (`turn started/ended`, `reasoning`, `message`, `command` with its output tail, `image`, `operator` = a
  pushed report), `src: robot` (robotd requests: `command` with the motion's robot-clock `t0`/`t1`, `reachable`, `ik`,
  `finish`, `park`), `src: queue` (the queue journal's events), `src: program`.
- `queue.jsonl`: the action queue's journal (`workspace/.robot/events/queue.jsonl`), see below.
- `AGENTS.md`: what the agent was told (task, environment, the queue, the cell, the manual).
- `profile.json`: where the time went (model, tools, motion, images); `verdict.json`, `meta.json`: the run's check
  and settings. The towel checks have no size threshold, so the operator judged those (`success: null`).

The live camera streams are not included (the folders would be ~100 MB to 1 GB each); the timeline videos in
`docs/demos/` show the front and wrist cameras in sync with the lanes.

## Reading the queue journal

The agent queues named actions (Python functions that command the arms) and keeps working while they run; the queue
starts each one as the previous ends. `queue.jsonl` has one line per queue event, all with `wall` (Unix time; subtract
`meta.json`'s start or use `timeline.jsonl`'s `t` for the same event to get seconds from the start), and with `running`
(the id now running, or null) and `waiting` (ids queued behind it, in order) as they are just after the event:

| `event` | Extra fields | Meaning |
|---|---|---|
| `queued` | `id`, `name`, `behind` (the id it waits for), `timeout`, `replace_from` | The agent added an action while another ran. |
| `started` | `id`, `name` | The action began commanding the arms (straight away if the queue was idle). |
| `ended` | `id`, `name`, `status` (`done in 14.3 s` or the error), `ok`, `t0`, `t1` (wall time it ran), `commands` | The action finished or was refused. A refusal (`ok: false`, e.g. `InvalidCommand: ... unreachable`) leaves the arms holding. |
| `look` | | A look (camera grid pushed to the agent) taken while an action ran. |
| `dropped` / `flushed` / `stop` | `id`, `name`, `why` | Waiting actions discarded (after a failure ahead of them, or by the agent). None occur in these three runs. |

The robot is moving exactly while some action runs, so the union of the `ended` events' `[t0, t1]` is the robot's
motion time (it matches `profile.json`'s `robot_moving_s`), and `len(waiting)` over time is the queue depth. A
`started` line for the next action usually comes a few ms before the previous one's `ended` line: the queue starts the
next action at the previous one's `t1`, then writes the end record. Each start, end and look is also pushed to the agent
as a report; those reports are the `operator` events in `timeline.jsonl` and user messages in the rollouts.
`docs/demos/data/<run>-lanes.json` has these intervals already computed.

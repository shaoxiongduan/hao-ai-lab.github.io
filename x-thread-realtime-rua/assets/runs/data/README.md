# Lane data for the demo videos

`<run>-lanes.json` (schema `robotapi.demo-lanes.v1`): the intervals behind the timeline videos
(`docs/demos/<run>-timeline-<speed>x.mp4`), for cups-02, towel-fold-18 and towel-fold-23. All times are seconds from
the run's start (`t` in `traces/<run>/timeline.jsonl`); `wall0_unix + t` is the Unix time.

```
{
  "schema": "robotapi.demo-lanes.v1",
  "run": "cups-02",
  "task": "short title", "instruction": "the full task text",
  "model": "gpt-6-astra", "reasoning_effort": "medium", "service_tier": "ultrafast", "codex_version": "codex-cli 0.165.0",
  "video_speed": 2.5,                 # speed of the timeline video
  "wall0_unix": 1794358308.0,
  "t_end": 213.8,                     # end of the episode shown: the agent's last turn ended + 1 s (just after r.finish;
                                      # the harness's 60 s linger afterwards is left out)
  "turns": [[t0, t1], ...],           # Codex turns (agent active)
  "robot_actions": [                  # ROBOT lane: one per queued action, in order; the robot moves while one runs
    {"id": 1, "name": "lift_left_cup", "t0": 28.2, "t1": 42.5, "ok": true, "status": "done in 14.3 s",
     "queued_t": 28.2,                # when the agent queued it (= started, if the queue was idle)
     "commands": 5}],                 # ok false: refused (status holds the error)
  "agent": [                          # AGENT lane: covers [0, t_end] without gaps, sorted by t0
    {"t0": 1.66, "t1": 5.30, "state": "thinking"},       # waiting for the model's first token + generating
    {"t0": 5.30, "t1": 5.35, "state": "tool", "tool": "exec", "kind": "reading files",
     "cmd": "first 160 chars of the shell command"},
    {"t0": 0.0, "t1": 1.66, "state": "idle"}],           # between turns
  "reports": [                        # pushed reports (instants); kind: started | done | error | look | other
    {"t": 28.3, "kind": "started", "action": "lift_left_cup", "text": "[action lift_left_cup] started ..."}],
  "queue_depth": [[t, n], ...],       # step function: n actions waiting (not counting the running one) from t on
  "messages": [{"t": 4.9, "text": "..."}],              # the agent's commentary messages
  "totals": {
    "wall_s", "finish_t", "first_motion_t",
    "robot_moving_s", "robot_moving_pct",                # pct of wall_s
    "robot_moving_pct_first_motion_to_finish",
    "model_thinking_s", "tool_s", "agent_busy_s" (thinking + tool), "agent_idle_s",
    "overlap_busy_moving_s",          # agent busy while the robot moved: model/tool time hidden behind motion
    "overlap_thinking_moving_s",      # the same for thinking only
    "robot_idle_while_agent_busy_s",  # the robot waiting on the agent
    "actions", "actions_failed", "queue_max_depth", "tool_calls", "reports", "turns", "threads"}
}
```

How the lanes were derived:
- ROBOT: the queue journal's `ended` events (`t0`, `t1`). Their union is the robot's motion time; it equals
  `profile.json`'s `robot_moving_s`. Dry-run checks (`dry_run=True`, `reachable`, `ik`) are not motion and are not shown.
- AGENT `tool`: each tool call in the Codex rollouts, from the `custom_tool_call` / `function_call` item (the model
  finished writing the call) to its `*_output` item (the result came back). `kind` is a rough label from the code.
- AGENT `thinking`: the rest of each turn (turns from `codex/events.jsonl`'s `turn.started` / `turn.completed`), i.e.
  the model's request in flight: upload, queueing, prefill, first token, decoding of reasoning, messages and tool calls.
  The rollouts cannot split waiting from generating; `profile.json` estimates the split (`first_token_s_est`,
  `decode_s_est`) at 282 tokens/s decode.
- AGENT `idle`: outside turns (a few tenths of a second at thread switches and at the start).
- `reports`: `codex/events.jsonl`'s `action.message` events (the harness delivering a report into the conversation).
- `queue_depth`: `len(waiting)` after each queue journal event.

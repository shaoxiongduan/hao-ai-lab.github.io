# Task

A blue towel lies on the table between the two arms, partly folded over. Spread it out flat, then fold it once in half, edge to edge. Leave it lying folded on the table, then call r.finish() with a short summary.

General advice (use your judgement):
- Grasping cloth: bring the open fingers to a place where cloth ends up between them just by moving toward it, then close. On a raised edge or fold, come down from above with the fingers across it; on a corner lying flat, scoop: tilt the hand so the lower finger slides in under the cloth. Prefer corners that are easy to reach. Check the point cloud and a ghost of the planned pose first, and the wrist camera after closing (a close on nothing ends near 3 mm wide).
- Spreading: grab two adjacent corners of one edge and pull back toward you, so the towel drags out flat. Don't swing or throw it.
- Folding: carry the two corners of one edge over onto the opposite two, lower them there and release. Check the result in the cameras and fix it if it is off.
- Keep the towel in the middle of the table where both arms reach well, each hand on its own side.

# Environment

- **The world** is the real robot cell described in "The real cell" below (`docs/REAL_CELL.md`): two YAM arms on a
  table, with four cameras (top, front, and one on each wrist). It runs on the wall clock: anything you leave moving
  keeps moving while you read, think or write code, and someone may be watching remotely who can stop or park
  the arms at any time.
- **Working directory:** `/workspace`, a git repository; this file is `/workspace/AGENTS.md`. Only `/workspace`
  and `/tmp` are writable.
- **Python** (nothing can be installed; `PYTHONPATH` is `/opt/robot-api`, so it can `import robot`):
  `/home/shao/robot-api-real/.venv/bin/python` (first on `PATH`, as `python`): numpy, scipy, OpenCV (`cv2`), mujoco, mink, ruckig, pillow. No
  torch, JAX, Pinocchio or Open3D. `ffmpeg` is on `PATH`.
- **No GPU.**
- **Memory:** a process that uses more than 3 GB of RAM is killed at once, and so is the largest of
  yours when all of them together use more than 4 GB.
- **No internet:** your programs can connect only to the robot's two sockets (the driver, and the cameras
  behind `r.cameras()`). No other network is
  reachable, whatever the sandbox settings say.
- **The robot:** `import robot; r = robot.connect()` connects through `$ROBOT_ADDR` (`unix:/run/robot-api/robot.sock`). Every file
  `r.description` names (URDFs, the MJCF and their meshes) is readable.
- **Code:** `/opt/robot-api`, read-only: `robot/` (the robot client), `robotd/core/` (the driver's control core) and `docs/` (`REAL_CELL.md` describes this cell and `MANUAL.md` the robot; both are copied below).
- **Before you start,** read all of the code in `/opt/robot-api`, every file in `robot/` and `robotd/core/`:
  the descriptions below summarise it, and the code says exactly what each call does and what it gives back.
- **Time:** 0.25 hours of wall-clock time from the start of the episode (2026-11-11T01:49:57Z UTC); `date` gives the time. At the
  limit the episode ends wherever things are.
- **Messages from the cell:** `python -m robot run` starts a program in a process of its own, which keeps running
  after the command returns (see the manual); when it pauses or ends, a `[program] ...` message comes into your
  turn. When the operator stops, parks or releases the arms, an `[operator] ...` message says so.
  As an action you queued ends, an `[action NAME] ...` message brings its report.
- **Ending:** call `r.finish(summary)` when you are done, then stop. The episode ends when you stop or at the time
  limit. Nobody answers questions during the episode, and no success signal comes back.

# Before you act

- **Think through the physical consequences.** For each action you consider, picture the whole motion, not only
  where it ends: what each finger touches first, what gets pushed, dragged, folded or knocked over on the way, where a
  held object swings, and what state it leaves for the next step. Name what could go wrong. Choose the option that is
  most likely to work and easiest to recover from when it does not, and change the plan when what you see says it
  will not work.
- **Grasp deeply.** A grasp holds by how much material is between the pads. Closed on the last millimetres of an edge
  or a corner tip, it slips or tears free. Aim so the pads close well inside the edge, with most of their height on
  the material, and approach from a side where neither finger pushes the material away before it is between the
  jaws. After closing, confirm the hold (a short lift, then look) before building on it, and do not let go of a hold
  you would have to redo until its result is confirmed.
- **Review before you commit.** Before a grasp or a motion that is hard to undo, look at it with `robot.viz`: the
  ghost in the camera images, and the 3D views of the point cloud (`jaws`, `along`, `approach`, and from the side),
  where the depth of the grasp, the fingers' clearance and contact are visible. For a motion with several stages,
  review its key poses together.

# Time, steps and images

- **Each of your steps is a model round trip of about 1 to 3 s,** longer the more images the conversation holds; the
  arms and the world keep going meanwhile.
- **A fresh `python` per command costs about 0.3 s** (start and imports), more the first time a ghost loads the arm
  model. `python -m robot.kernel` runs code in one long-running Python instead (a call starts in about 40 ms): stdin or
  a file, one namespace that persists between calls (robot, np, cv2, viz, watch, when and kernel imported; your
  variables, functions and loaded data stay), and each call ends as a program does: its robot connections close
  (their motions stop) and it prints its `[state]` and `[views]` lines. `python -m robot.kernel --help` says more.
- **Every image in the conversation slows every later step,** by the number of images and their size. One image of
  several cameras costs less than one per camera: `viz.show_cameras(name, r)` shows every camera as one labelled grid
  (`viz.grid` tiles any images). A smaller image costs less (`viz.show_cameras(name, r, width=640)`). Attach images
  at the default detail: this Codex drops an image sent with detail "low" (the model gets a note instead). The
  harness moves the conversation to a fresh thread after many images: older images become notes naming their
  files, which you can view again.
- **A command's images can come back in the step that ran it.** A program that showed images prints
  `[views] ["/path/a.png", ...]` (one JSON list) as it exits, so the same exec cell can attach them, e.g.
  `const o = (await tools.exec_command({cmd, yield_time_ms: 20000})).output; text(o);`
  `for (const p of JSON.parse((o.match(/^\[views\] (.*)$/m) || [, "[]"])[1])) image((await tools.view_image({path: p})).image_url);`
  Viewing them in a later step costs another round trip.
- **A program that moved the arms prints `[state] ...` as it exits:** where each arm ended, its gripper's width and
  whether it is holding something, contact, any fault.
- **A command that runs longer than its `yield_time_ms` returns early,** and seeing how it ended takes another step;
  with a `yield_time_ms` longer than its motions, it all comes back at once. `python -m robot run` programs report
  when they pause or end (`[program] ...`, with their `[state]` and `[views]`), with nothing to check on.
- **While a motion runs, your time runs too.** `kernel.queue(fn)` (below) runs a whole action while your steps go
  on; a motion started with `wait=False` returns at once too (its `.result()` waits for it, within the same
  call). `robot.watch` renders, while a motion runs and
  without holding it up, one compact image per arm about once a second (`views/monitor-*.png`: the wrist and front
  cameras with the arm's ghost where it is, and the point cloud's `jaws` and `along` views) with a line of what is
  between the jaws, and can stop the motion through a signal (`until=when.signal("watch") > 0`) when your check
  says so.
- **`viz.marks(frame, name, mask=...)` numbers points on a camera image** and returns their world positions, so a
  place can be named by its number instead of measuring pixels and looking up depth in another step.
  `on_table=True` keeps only what lies over the table (whatever is around and beyond it is left out).

## Keep a queue of actions, and keep looking while the arms work

The arms do not wait for you if the next action is queued before the running one ends: an action's end and the next
one's start are one moment, with no step of yours in between. You work the whole time they move, on the newest view.

- **Write the action as a function and queue it.** `kernel.queue(fn)` runs `fn(r)` in your kernel (`r`: the actions'
  robot connection) and returns at once. With nothing running it starts now; with an action running it starts as the
  last one queued before it ends. `kernel.queue([f, g])` queues several in order. At most three wait.
  ```python
  def grasp(r):
      r.gripper('left', .07); r.move(A, ee='left', duration=3); r.move(G, ee='left', line=True, duration=3)
      r.gripper('left', w - 0.003, speed=0.02, force=30); r.move(L, ee='left', line=True, duration=3)   # w: its width
  kernel.queue(grasp)
  ```
- **Messages come to you without a step of yours.** Each is the state of things now; it reaches your running turn at
  your next step, or starts a turn.
  - As an action ends: its report, `[action A] done in 9.8 s`, what it printed, `[queue] started: B (#14; ...)`,
    the arms' `[state]`, every camera as one grid (`views/after-A.png`, attached) and your after-motion hooks. The grid
    is taken as B starts, so it shows what A left.
  - Each time your turn ends while an action runs: a look, `[look N]`, with `[state]`, the grid (`views/look-N.png`,
    attached) and the queue, from that moment. Fetching the cameras yourself costs a step.
- **Every message says where the queue stands:** `[queue] running #14 grasp: 3.1 s in, command 3 (move)`, then
  `[queue] waiting 1: #15 lift`, `[queue] waiting 2: #16 lay` in order. `[queue] empty behind it` means the arms stop
  after the running action unless you queue one.
- **With each message, the queue is yours to change.**
  - Add: `kernel.queue(fn)`.
  - Change an item: `kernel.queue(new, replace_from=15)` takes #15 and everything behind it out of the queue and puts
    `new` in their place, in one step, since what stood behind it was planned on it. To replace more than one, pass a
    list: `kernel.queue([f, g], replace_from=15)`. If #15 has started by then, nothing changes and it raises.
  - Drop: `kernel.flush(from_item=15)` drops #15 and what is behind it; `kernel.flush()` drops the whole queue.
  - If what is queued still makes sense, keep working: write the action that comes after the last one and add it, from
    what you have and the code ahead of it, even with the running action unfinished. Each look is the moment to write
    the next action, not a check on this one. Only when three actions wait and all of them still make sense is there
    nothing to write: then end your turn, which costs the arms nothing, and the next look or report comes.
- **What you see is older than what is happening.** The newest picture shows the moment it was taken, and the running
  action has gone on since. What you queue starts from where the actions ahead of it leave things: you know their code
  and where they end the arms.
- **Code you queue runs later, so what it reads is newer than what you saw.** `r.state()` and `r.cameras()` inside `fn`
  are read as it runs, so a next move that depends on how the cloth lands can compute its target there, or open with a
  move that is useful either way. A check at the top of `fn` that raises ends it before it moves.
- **If an action ends with an error or is stopped, everything queued is dropped** (`[queue] dropped: B`) and the arms
  hold, so what you planned on its success does not run.
- **Wrong plan while the arms move:** `kernel.action().stop()` halts every motion at once (the arms hold where they are),
  its code goes no further and the queue is dropped; its report still comes.
- **Ending the episode:** with nothing running or queued, ending your turn ends it. Do not wait on an action, sleep or
  poll: each of those is a step that only waits.
- **Give every kernel call a long `yield_time_ms` (60000).** A call returns as soon as its code ends, and `kernel.queue`
  returns at once by itself.
- **What stays as it is:** the driver checks every command (reach, fence, the arms' separation) as it is sent; an
  action's error comes in its report (`[action NAME] error ...`). A call that sends the arms a command stops the running
  action first; its timeout (120 s, `kernel.queue(fn, timeout=...)`, counted from its start) stops it too.

## Make the tools yours: every step should end with what the next one needs

The robot API is yours to extend while you work. Functions you define in your kernel stay for the rest of the
episode, and hooks you register run at the end of your calls with their output in that call's own result, so you can
shape what each command does and returns to fit the task. Use them to need fewer steps: each step is a model round
trip, and one that only fetches something costs as much as one that acts.

- **Hooks run at the end of your calls.** `kernel.after_motion(fn)` runs `fn(r, frames)` at the end of every kernel
  call that moved the arms (`r`: the call's robot; `frames`: one grab of every camera with depth, taken when the hook
  first reads it); what it prints and shows comes back with the motion's result. `kernel.after_call(fn)` runs after
  every call. If you find yourself fetching the same thing after motions (the object's numbered points, a wrist
  view, a check of what is between the jaws), make it a hook, e.g. once the towel's colour is known:
  ```python
  def towel(r, frames):
      f = frames['front']; h = cv2.cvtColor(f.rgb, cv2.COLOR_RGB2HSV)
      viz.marks(f, 'towel', mask=(h[..., 0] > 85) & (h[..., 0] < 120) & (h[..., 1] > 90), on_table=True, picture=False)
  kernel.after_motion(towel)
  ```
  From then on every call that moves the arms ends with `[marks towel] 1:(x,y,z) ...`. Registering a function of the
  same name again replaces it (`kernel.remove_hook(name)`, `kernel.hooks()`).
- **Helpers: write once what you repeat.** A grasp sequence, the review picture you draw before each move, a
  check you keep making: define it as a function in the kernel and call it by name. Shorter calls are quicker to
  write, and the same function runs the same way every time.
- **Keep hooks quick and their output short.** Every call that moves pays for every hook, and what a hook prints
  stays in the conversation: points as text cost little (a mask and its points take about 0.1 s), a 3D render
  0.5-1 s, and each image slows every later step. A hook that raises prints `[hook NAME] error ...` and never fails
  the call.
- **Change them as the task changes:** replace a hook when you need something else watched, drop it when you no
  longer do.
- **What stays as it is:** the driver's limits (the fence, the arms' separation, speed and force limits) are outside
  your kernel, and apply to everything as before.

# The real cell

This is the real YAM cell the robot API drives. The robot manual describes the station as simulated; where this
description, `r.description` or your own measurements differ from it, they win. The numbers here were measured on this
cell in November 2026; the camera figures come from 110 saved frames of three episodes.

## Layout

- **Arms.** Two I2RT YAM arms, `left` and `right`, on one table, in the manual's world frame: origin on the table top
  midway between the bases, +x forward (away from the bases), +z up.
- **Bases.** The left base is at (0, +0.305, 0). The right base is not where the simulated one is: the cell's
  calibration puts it at (-0.013, -0.208, +0.015), 9.7 cm closer to the left in y and 1.5 cm higher, turned 2.4
  degrees. `r.description["arms"][arm]["T_world_base"]`, the URDF and the MJCF in `r.description["files"]` all have
  the calibrated bases: they are the driver's own model, so forward kinematics from them agree with `r.state()`.
- **Joints.** The calibration also corrects each joint's encoder zero (by up to about 3 degrees). The joint angles
  `r.state()` reports, and those you command, are already corrected: they mean what the model files mean.
- **The table.** Light wood; the arms' work area spans about x 0.1-0.8 m. Its top reads between 3 and 13 mm above
  z = 0, depending on the camera (see Cameras); the driver's model puts it at about 5 mm. Overhead lights
  make a bright glare patch on it in the fixed cameras.
- **Around the table.** Off its edges the cameras see the floor, light stands and the cell's frame. Beyond the table
  there is a blue backdrop.
- **Time.** Everything runs on the wall clock. Anything left moving keeps moving while you read, think or write code.

## Cameras

Four Intel RealSense RGB-D cameras. Colour and depth are both 640 x 480, depth registered to colour (one `K` per
frame), streaming at 30 frames a second; `r.cameras()` returns the latest frames.

| Camera | Sensor | Where | Field of view | Sees on the table |
|---|---|---|---|---|
| `top` | D435i | fixed at (0.77, 0.42, 0.86), looking straight down | 56 x 43 deg | x 0.26-0.77, y 0.04-0.59: the left half only. The right arm's side is outside it. |
| `front` | D435i | fixed at (0.06, 0.09, 0.98) above the bases, looking forward, 70 deg below level | 56 x 43 deg | x 0.11-0.76, y -0.53-0.54: the whole table, at a slant |
| `left_wrist` | D405 | on the left gripper, moving with it | 79 x 63 deg | wherever the gripper points |
| `right_wrist` | D405 | on the right gripper, moving with it | 79 x 63 deg | wherever the gripper points |

**Depth and point-cloud precision**, measured on the bare table in 110 saved frames:

| Camera | Pixels with depth | Distances in view | Table height | Table tilt | Scatter about the table (sd / 95%) | One pixel covers |
|---|---|---|---|---|---|---|
| `top` | 95% | 0.6-1.7 m | 3.4 mm | 0.6 deg | 3.6 / 7.0 mm | 1.4 mm |
| `front` | 94% | 0.5-1.7 m | 13.3 mm | 0.4 deg | 5.6 / 11.4 mm | 1.7 mm |
| `left_wrist` | 82% | 0.07-0.39 m | 7.6 mm | 3.2 deg | 2.5 / 5.0 mm | 0.5 mm |
| `right_wrist` | 84% | 0.07-0.38 m | 13.4 mm | 2.1 deg | 1.7 / 3.4 mm | 0.7 mm |

The table is flat, so each column shows a camera's error:

- **Absolute height.** The same table comes out between 3 and 13 mm high depending on the camera.
- **Between cameras.** Laid on `top`'s cloud, `front`'s fits best shifted by (+2, +8, -9) mm, about 12 mm in all, and
  that shift is steady from frame to frame. The wrist cameras' clouds sit 5-10 mm from the fixed cameras', and their
  offset changes with the arm's pose (by about 1 cm from one frame to another), because a wrist camera's pose comes
  from the arm's joint readings. A point seen by one camera is therefore placed in the world to about 1-2 cm.
- **Tilt.** The wrist cameras see the level table tilted 2-3 degrees. That is an error in their orientation: across a
  10 cm patch it makes a false slope of 3-5 mm, and more further away. The fixed cameras are within about 0.5
  degrees, about 1 mm per 10 cm.
- **Within one camera.** Points on a flat surface scatter about it by the amounts in the table: a few mm for the
  wrist cameras, 4-6 mm for the fixed ones, with one point in twenty further off. Relative positions within one wrist
  camera's view are good to a few millimetres: it separates steps of about 3 mm close up. A thin layer of a few mm on
  the table is within the fixed cameras' scatter.
- **Edges.** One pixel covers the size in the last column at the camera's working distance, and an edge blurs over a
  couple of pixels. Where the depth jumps (an object's edge against what is behind it), single points can float
  between the two surfaces.
- **The wrist cameras.** The D405 reads depth from about 7 cm; nearer than that is blank. The fingertips are about
  9 cm in front of the camera, so what they touch is in range. The TCP falls near pixel (331, 385) in `left_wrist`
  and (313, 369) in `right_wrist`. The fingers fill part of the bottom of the image and hide what is between them
  from the camera's side. The camera moves with every motion of its arm.
- **Gaps.** Missing depth is most common on dark or shiny surfaces, at depth edges, and nearer than a camera's
  minimum range (7 cm for the wrist cameras).

**Recordings.** From the start of an episode, every camera's colour is recorded, a few frames a second (6 in recent
episodes), in `/var/record/cameras`: one MP4 per camera, with each frame's wall time in `frames.csv`. A few times a
second (3 by default) every camera's colour and depth from one grab are recorded too, with K and the camera's pose
(`rgbd/`, indexed in `rgbd.jsonl`). `robot.recording.Recording()` reads the recordings by time (`frame_at`,
`frames`, `clip`; `cameras_at` returns an RGB-D grab as frames like `r.cameras()`, which `robot.viz` takes), and
`ffmpeg` is on `PATH`. A pause's `pause-N/` also has depth.

## Arms

- **Stopping short.** An arm stops short of a commanded pose in the direction it moved: about 1 cm after a move down,
  and up to 3 cm after a move up (the manual's ~4 mm is the simulation). `r.state()` says where it really is.
- **Force.** The arms have no force sensor, and their derived force and wrench estimates (`s.ee[arm].force`,
  `when.force`, `contact`) are not reliable here. The raw signals are there to read and judge for yourself
  (`s = r.state()`, joints in `s.joints` order):
  - `s.q - s.q_cmd`: each joint's tracking error (rad). Joint friction alone holds a joint anywhere within about
    0.4-0.8 deg of its command on joints 1-3 (kp 80 Nm/rad, so ~1 Nm); a joint pushed or blocked falls further behind.
  - `s.effort()`: the motors' measured torque (Nm, gravity included); `s.effort_ext()`: that minus the model's
    gravity (about +-1 Nm of friction and model error at rest).
  - `s.ee[arm].deflection`: the TCP's measured minus commanded position (m).
  - The grippers' width and effort (`s.grippers`) are reliable.
  Compare against a baseline taken just before (the same pose, not moving) rather than against zero.
- **Gains.** `gains=` is capped at the defaults (`r.description["max_gain_scale"]` is 1). Stiffer than that, the arm
  chatters against what it presses on.
- **Speed.** The joint speed limits are in `r.description["max_velocity"]` and `["velocity_limit"]`.
- **Reach.** Measured by sampling the arm's model, in each arm's own base frame:

  | Gripper | TCP height | Reach at table height |
  |---|---|---|
  | jaws straight down | up to about 0.22 m | about 0.50 m forward |
  | tilted 35-60 deg from vertical | up to about 0.48 m | about 0.73 m |
  | sideways | up to about 0.7 m | |

  In world terms, with the jaws down at table height, the left arm reaches y from about -0.15 to +0.55 and the right
  from about -0.50 to +0.20, out to x of about 0.45. The fence (below) narrows this to each arm's half of the table.

## Grippers

- **Opening.** 0-94 mm between the pads; `force=` up to 50 N per pad (the default).
- **Squeeze.** The width target sets most of the squeeze. The jaws are stiff: each mm the target lies inside the
  object adds roughly 90 N. `force=` takes hold only once the jaws are blocked and moving slowly. A target of 0 on a
  wide object (a 6.7 cm ball at full speed, 2026-11-04) crushed it to 37 mm at up to 307 N before the overload guard
  aborted the grasp (`gripper_overload`).
- **Closing on a thin layer.** A gripper's width and its stall flag cannot tell a thin layer (one layer of cloth)
  from an empty close: both end near 2.9 mm, and `stalled` is unreliable there. Something thick enough to stop the
  jaws shows as `stalled` with that width.
- **Seeing the jaws.** The wrist cameras look at the jaws from 9 cm, and `robot.viz` (in the manual) can draw the
  fingers where a move would put them, mark what lies between them, and count it.

## Safety limits, always on

- **The fence.** Each arm's TCP is kept in a box over its half of the table, and the TCPs' speed in the table plane
  is capped. Both are in `r.description["fence"]`; in the towel episodes the box was x 0.12-0.70, y 0.05-0.50 for the
  left arm and -0.45-0.05 for the right, z up to 0.65, at 1 m/s.
  - A command that would leave the box, or go faster, is refused with `robot.InvalidCommand`.
  - The box's floor bounds only the TCP. A tilted gripper's fingers and body reach below it, so the fence's
    `gripper_floor` (4.5 mm) bounds the whole gripper: a target that would take any part of it lower is refused.
  - The manual's "The workspace fence" section has the details.
- **Separation.** The two arms are kept at least 2 cm apart, measured between capsules around their links and
  grippers (`r.description["separation"]`). A command whose goal is closer is refused (`robot.InvalidCommand`). An arm
  that moves closer stops, and its command ends `aborted` with the reason `separation: ...`.
- **The operator.** Someone may be watching remotely and can stop or park the arms at any time. Until they release
  them, every command is refused with `robot.Fault`.

# Robot manual (agent-facing)

You control a robot by writing and running Python. `import robot; r = robot.connect()` gives you the robot. Everything
else is ordinary Python, with whatever libraries are installed. When this manual is unclear, read the code:
`robot/__init__.py` (the client) and `robotd/core/controller.py` (what the driver does every 4 ms).

This manual describes the station as simulated. A real cell comes with a description of its own (its layout, its
cameras as measured, how its arms and grippers behave), and where the two differ, the cell's description, `r.description`
and your measurements win.

## The robot: bimanual I2RT YAM station

| Part | Facts |
|---|---|
| Arms | `left`, `right`: 6 revolute joints each (`left_joint1..6`). Bases at world (0, +0.305, 0) and (0, -0.305, 0). Reach about 0.6 m from the base. Joint limits are in `r.description["files"]["urdf"]` (see Using libraries). |
| Gripper | Linear, two fingers. Opening 0–0.094 m between the pads. `r.gripper(arm, width, force=N)`: N is each pad's squeeze (at most 50 N, the default). A grasp that stops on an object ends with reason `stalled`, and `Result.width` is what it holds. Each fingertip's face is 12 mm wide at its end and 25 mm wide 15 mm up, with a window in its middle above that. |
| Tool point (TCP) | The centre between the fingertip pads (site `tcp_left`/`tcp_right`). With the jaws closed the pads meet there. Poses you command are TCP poses unless you pass `tcp=` (a 4x4 offset from the TCP, e.g. to a tool tip). |
| Cameras | `top` (overhead, looking down at the table), `left_wrist`, `right_wrist` (D405 RGB-D cameras that move with their grippers). Colour and depth, 640 x 480: see Cameras and point clouds below. |
| World frame | Origin on the table top midway between the bases; +x forward (away from the bases), +z up. The table top is z = 0. |
| Reachability | Jaws straight down (`rpy=[pi, 0, pi]`) reach the whole table area x 0.2–0.5 m in front of a base when the TCP is at most ~0.10 m above the table; higher than that, tilt the jaws about 20° toward +x. An unreachable goal raises `InvalidCommand` with the IK miss distance. When some axes do not matter, leave them to the driver with `free=` (below) instead of trying poses one by one, and when they do, check the candidates together with `r.reachable` rather than moving to one and reading the refusal. `r.ik`, `r.reachable` and `r.move(..., dry_run=True)` ask without moving. |
| Accuracy | The wrist is soft (gains kp 10): a moving TCP lags its reference by up to ~1 cm, and settles within ~4 mm (a still arm's steady offset, from the gravity model, is integrated away within ~1 s: `r.description["settle_bias"]`). Do not rely on mm-level position accuracy; use guarded moves (`until=` conditions) to find surfaces. A quick path (a stroke under ~0.2 s) lags more, a few cm and degrees at a tool 10 cm out, and a held tool's weight sags the wrist (a 0.14 kg paddle: ~1 cm, ~1.5 deg): `r.state()` says where the tool really is, so measure and compensate. Near a joint limit or a straight elbow, small tool motions need large joint motions and track worst. |
| Speed | Joint velocity limits are in `r.description["velocity_limit"]` (rad/s): 3 on joints 1-3, 4 on the wrist. A joint path faster than that is refused with `InvalidCommand` (the message says how much to stretch the times). Turning a held tool over (wrist roll, joint 6, half a turn) takes at least 0.8 s. |
| Force | There is no force sensor. Force is estimated from joint torques: about ±0.5 N in simulation and ±1–3 N on the real arm. Call `r.zero_force(arm)` just before contact and after grasping. On the real arm, deflection (`when.deflection`, encoder only) is the more reliable contact signal under a soft compliance. Rely on force as little as you can: as a stop when something is touched, not to align, insert or place by feel. |
| Timing | Simulation is paused whenever your code is not inside a blocking call or `r.step()`, so thinking costs no time. On the real robot time keeps running: a slow loop is a slow robot. `r.lockstep` says which (a simulation can also run in real time, like the robot). |
| Workspace fence | When the driver runs with one (`r.description["fence"]`, else `None`), each fenced arm's TCP must stay in its box, and the TCPs' speed in the table plane is capped. See below. |

## The calls

| You want to | Call |
|---|---|
| Look | `f = r.cameras(["top"])["top"]`, then `f.rgb`, `f.depth`, `f.points(mask)`; `roi=` for a window |
| Read the robot | `s = r.state()`: `s.q(names)`, `s.ee["left"].T` / `.v` (TCP linear velocity, 3 values, m/s, world) / `.force` / `.contact` / `.deflection`, `s.grippers["left"]` (`width`, `stalled`: closed on something, `empty`: closed on nothing). `.contact` comes from the arms' force estimate: `r.description["arm_force_trusted"]` is False on the real arm (it read contact with the hand 30 cm in the air), and the `[state]` line leaves it out there |
| Go to a pose | `r.move(T, ee="left")`: there and stop, smoothly (`line=True` for a straight line, `speed=` m/s, `duration=` s) |
| Leave axes free | `r.move(T, ee="left", free="yaw")`: any turn about the tool's z axis (a top-down pinch); `"yaw180"`: as given or half a turn more (the same grasp for a parallel gripper); `"rotation"`: position only. The driver picks the solution quickest to reach that keeps away from joint limits (along a path, the turns that make the whole path cheapest, without wrist flips); `res.goal["left"]` is the pose it chose |
| Go to joint angles | `r.move(q, joints=names)` |
| Follow a path | `r.move(poses, ee="left")` passes through them, timed from the speed limits (`speed=`; `duration=` for the whole path), or at `times=[...]` (s from the start, one per pose) or `dt=`. `velocities=`: the controlled point's m/s at each pose, to pass a pose at a time with a speed; `relative=True`: offsets from the start; `free=` one value or one per pose |
| Run a planner's path | `r.move(qs, joints=names, dt=0.02)` or `times=`, `velocities=` (rad/s per point) as the planner gives them (numpy, torch or JAX). A first point that is the current state (at t=0, or the first of dt-spaced points) is dropped; a point outside the joint limits or too fast is refused, naming the point, the joint and the limit |
| Servo on something moving | re-send short paths in a loop: `r.move(T, ee="left", times=[tau], velocities=[v], wait=False)`, tau 2-3x the loop's period (0.08 s at 30 Hz). Every move continues from the arm's current position, velocity and acceleration, so re-sending is smooth |
| Check before moving | `r.ik(T, ee="left", free=None)` → `{"joints", "q", "ok", "error_m", "T", "margin"}`; `r.reachable([T1, T2, ...], ee="left", free=..., line=False)`: many candidates in one call (approach angles, tilts, heights), each checked as `r.move` would check it (fence, gripper floor, IK, separation from the other arm where it is commanded and where its running move ends; `line=True`: the straight line too), with `why` the refusal it would get, None when `ok` (filter on `ok`, rank by `margin`); `r.move(..., dry_run=True)` → a `Plan`: ok, or where a line or path would fail (point, fraction of its leg, pose, miss) and the tightest margin on the way (`limit_rad` to the nearest joint limit, `singular_m` near 0 at a straight elbow) |
| Move until something happens | `r.move_at({"z": -0.02}, ee="left", until=when.force("left", "-z") > 3)`; `max_travel=` m (default 0.30) ends it with reason `max_travel` |
| Find a surface | the guarded move above with `until={"contact": when.force(arm, "-z") > 3}`: reason `contact` or `max_travel`; `res.at.T["left"]` is where |
| Grasp / release | `r.gripper("left", w - 0.003, speed=0.02, force=15)` (w: the object's width) / `r.gripper("left", 0.08)` |
| Press with a force | any motion with `compliance=Compliance(frame="world", stiffness={"z": 500}, force={"-z": 5})` |
| Let time pass | `r.step(ticks)` (40 ms each), `r.step_until(t)` (to a robot time, in 4 ms ticks: a fixed-rate loop) |
| See a detection or a plan before acting on it | `robot.viz` (below): draw it on a frame, render the gripper where a move would put it, and look |
| Stop everything | `r.stop()` |
| End the episode | `r.finish("what you did and what you believe the outcome is")`. No success signal comes back: check with your own eyes (cameras) before you finish. |

Every motion call takes the same extra arguments:
- `until=` a condition, or `{name: condition}`. When it fires, the motion ends with status `stopped` and reason = the name.
- `then=` what comes next: another command or a list of them (built with `robot.Move/MoveAt/Gripper`), started when the motion ends as asked, whether it arrived or a condition fired (in simulation in the same 4 ms tick; on a real robot as soon as it is built, the arm holding meanwhile: a few ms for a goal, ~75 ms with `free="yaw"`, seconds for a long `free=` path); a dict picks by the reason (`{"contact": ..., "max_travel": ...}`). `"hold"` (default) and `("back_off", metres)` are reactions to an `until=` condition.
- `on={name: (condition, command)}` fires a command once without stopping the motion, e.g. open the gripper at 60% of a
  throw, or start the next motion of the same arm at a time (`when.time() > 0.4`): it takes over smoothly. A command
  that is refused as it fires (an `on=` or `then=` one) ends the command that fired it, `aborted` with the refusal as
  its reason (it raises `Aborted`), and the arm holds.
- `compliance=Compliance(...)` and `gains={"scale": 0.5}` or `{"kp": [...], "kd": [...]}`: joint stiffness for this
  command (a command without `gains=` runs with the defaults; one that ends holds with its gains until your next
  command on those joints).
  A compliant command that ends keeps its push (a press keeps pressing) until your next command on that arm;
  `then="hold"` stops pushing.
- `tcp=4x4` moves the controlled point: rotate about a hinge, or press with a tool tip.
- `start_at=` starts on the robot clock: what runs on those joints keeps going until then, and a timed path that arrives
  late keeps its waypoints on that clock. `replace=True` (default) lets a new command take over joints a running one
  uses, smoothly: it continues from the current reference and its velocity (resending a path mid-motion is fine).
- `wait=False` returns a handle (`.result()`, `.done`, `.stop()`); then step or wait to let it run.
- `timeout=` in seconds.

Conditions run in the driver every 4 ms, not in your loop:
- `when.force(ee, "-z")`, `when.torque`, `when.effort(joint)`, `when.deflection(ee, "z")`, `when.travel(ee, "-z")`, `when.pose(ee, "z")`, `when.speed(ee)`, `when.time()`, `when.progress()`, `when.contact(ee)`, `when.gripper(name).width` (compare it) / `.stalled` (already a condition: `until=when.gripper("left").stalled`), `when.signal(name)`;
- combine with `>` `<` `&` `|` `~` `abs()` `+` `-`, `.held(seconds)` and `when.after(first, then)`.

## The workspace fence

The operator can start the driver with a fence (`robotd --fence`, or a scene's own): a box per arm for its TCP and a
speed cap in the table plane, for working near people. `r.description["fence"]` shows it, e.g.
`{"left": {"x": [0.13, 0.54], "y": [-0.02, 0.19], "z": [0.11, 0.24]}, "right": {...}, "max_speed_xy": 1.0,
"margin": 0.02}` (metres, world frame; `null` leaves that end open; an arm left out is not fenced).
- A target outside the box, or a path point outside it, is refused with `InvalidCommand` naming the limit
  (`fence: the target: left TCP x 0.600 m > x_max 0.540 m`). So is a command that asks for more planar speed than
  `max_speed_xy` (`speed=`, a timed path's legs or `velocities=`, a `move_at` twist): stretch the times.
- A motion whose reference would leave the box on the way (a joint move that swings out) stops at the edge: it ends
  `aborted` with a `fence: ...` reason and the arm holds inside. The reference never moves faster than the cap in
  the table plane. A `move_at` toward a wall ends `done` with reason `fence` at the wall.
- The measured TCP outside its box by more than `margin`, or moving faster than 1.5 x the cap for 20 ms (pushed,
  struck), latches a `Fault`. `r.recover()` clears it; an arm outside its box may then only move back in.
- An arm starts outside its box (at rest): its checks start once its TCP is inside. Parking (the operator's PARK,
  the driver's exit) ignores the fence, and the arm's checks start again when it is back inside.
- `"gripper_floor": z`, when the fence has one, bounds the whole gripper, not only its TCP: the fingers, the body and
  the wrist camera stay above that height (the table). A tilted gripper's fingers and body reach below its TCP, so
  it meets this floor before its TCP meets the box's. A target or path point that would put the gripper lower is
  refused (`fence: the target: left gripper's lowest point z ... < gripper_floor ...`), and a motion whose reference
  would take it lower stops there (`aborted`), as at the box's walls.
- `r.description["max_gain_scale"]`, when set (the real robot: 1), caps a command's `gains=`: a `scale` above it,
  or `kp`/`kd` above the defaults times it (`kd` times its square root), is refused with `InvalidCommand`.

## Results and errors

- A command returns `Result(status, reason, t, duration, at)`. `status` is one of `done`, `stopped` (a condition fired), `replaced` or `timeout`. `at` is the state when it ended; `goal` the pose(s) free axes settled on.
- A condition firing is normal. Read `reason`.
- Exceptions mean something you did not ask for:
  - `Aborted` (the motion could not go on: the arm could not track its path, `cannot_track`; a `then=`/`on=` command was refused as it fired; a gripper jammed, `gripper_overload`). `e.result` is its Result and the arm holds where it is: look at what happened, then decide;
  - `InvalidCommand` (bad arguments, unreachable goal; the message says what);
  - `Fault` (a guard latched, e.g. `max_force`; the arm holds; call `r.recover()`). When the operator stops the robot,
    your running command ends `aborted` with reason `operator_stop` and every command raises `Fault` until the
    operator releases it; `r.recover()` cannot. Stop and report;
  - `Busy` (`replace=False` and the joints are in use);
  - `NotSupported` (this robot or backend lacks the feature asked for).
  All are subclasses of `robot.RobotError`.

## Cameras and point clouds

`r.cameras(names=None, depth=True, roi=None)` takes a frame from each camera named (all of them by default) and
returns `{name: Frame}`:

| Field | |
|---|---|
| `rgb` | H x W x 3 uint8 in RGB order (OpenCV's own functions expect BGR: `cv2.cvtColor(f.rgb, cv2.COLOR_RGB2BGR)`). |
| `depth` | H x W float32, metres along the camera's axis (the z of the point in the camera's frame, not its distance along the ray). 0 or NaN where there is no reading. It is registered to `rgb`: pixel (u, v) of both looks along the same ray, and one `K` serves both. |
| `K` | The 3 x 3 intrinsics of this image: fx, fy (pixels), and the principal point cx, cy. |
| `T` | The camera's pose, world <- optical: +z looks forward, +x is right in the image and +y is down. `None` when the camera has no calibrated pose (`pose_error` says why), and then `points()` refuses. |
| `t` | The robot-clock time the image shows. On a real robot the frame reaches you 10-50 ms later. |
| `roi` | With `roi=[u0, v0, u1, v1]` (one box, or `{name: box}`), only that pixel box comes back and `K` is shifted to match, so everything below works on the crop as on the full image. It is quicker to send and to search when you track something small. |

- **Pixel to world.** With `z = depth[v, u]`, the point in the camera's frame is `((u - cx) z / fx, (v - cy) z / fy,
  z)`, and `T @ [x, y, z, 1]` puts it in the world. `f.points(mask)` does this for every pixel of a boolean mask
  (`None`: all of them) and returns N x 3 world points; pixels without a reading are left out, and `stride=n` takes
  every n-th row and column. Keep the mask's pixel indices if you need to go back.
- **World to pixel.** `p = inv(T) @ [x, y, z, 1]`, then `u = fx p_x / p_z + cx`, `v = fy p_y / p_z + cy`; a point
  with `p_z <= 0` is behind the camera. `viz.Overlay(r, cam).uv(points)` does it for many points.
- **Fusing cameras.** Every camera's points are in the same world frame, so clouds from several cameras can be
  stacked. Each camera's pose is calibrated on its own, though, so on a real cell the same surface can sit a few
  millimetres to a centimetre apart from one camera to another. Compare shapes and heights within one camera before
  comparing single points across cameras.
- **What real depth cameras miss.** Black, shiny and transparent surfaces give no reading or a wrong one. So does
  anything nearer than the camera's minimum range. At an object's edge a pixel can mix the near and the far surface
  into a point that floats between them ("flying pixels"). Noise grows with distance, roughly with its square, and a
  thin layer on a surface (cloth, paper) is within that noise unless the camera is close. A simulated camera renders
  exact depth and has none of these.
- **Being seen.** The arms appear in the fixed cameras' images, and a wrist camera always sees its own fingers. A
  camera sees only the surfaces facing it: the underside of anything, and what the arm or an object hides, are not in
  its cloud.
- **Cost.** Each call sends whole images through the camera server: ask for the cameras you need, `depth=False` when
  colour is enough, and `roi=` in a tracking loop. In lockstep simulation no time passes while you look.

## Pictures: `robot.viz`

Pictures of what your code found and what it plans: drawn on camera frames, or in 3D from the cameras' point clouds,
with the arm rendered where a move would put it. They are image files you can open and look at, and the operator's
dashboard shows them too.

```python
from robot import viz
o = viz.Overlay(r, "left_wrist")          # a fresh frame from that camera to draw on
g = o.ghost("left", T, width=0.05)        # the gripper where r.ik puts TCP pose T, jaws 5 cm apart
o.point(p, "target")                      # world points (3 or N x 3), labelled
o.path([T_above, T])                      # the TCP's way there
o.mask(m, label="object")                 # a pixel mask of this image
o.show("check")                           # writes views/check.png and prints its path: open it and look
viz.show("depth", f.depth)                # any image: RGB, grey, bool, or a float map (coloured by value)
```

- `o.ghost(arm, target=None, q=None, width=None, free=None, parts=None, after=None)` renders the arm's own meshes at
  the joints `r.ik` finds for `target` (from `after=`, as for `r.reachable`, if given; or at joint values `q`, or where
  the arm is now). It is translucent where the camera
  would see it and **red where a surface the camera sees is in front of it**: there it would be inside or under that
  surface. The arms' own pixels where they are now are not counted as surfaces. A surface within about 6 mm (or 1% of
  its distance) of the ghost does not hide it. `parts`: `"fingers"` (the default in a wrist camera), `"gripper"`
  (the default elsewhere) or `"arm"`. It returns `{"ik_ok", "error_m", "q", "T", "pixels", "behind_fraction",
  "jaw_box", "between"}`, so code can use the result as well as you.
- **The arms' own points are left out** of `between` and of the 3D views' point cloud: depth points within 6 mm of
  where the model puts the arms now (12 mm in a camera that does not ride on the arm, whose view of the arm carries
  the arm pose's error) are the arms themselves (`viz.SELF_MARGIN`, `viz.SELF_MARGIN_FIXED`). An empty gripper reads
  0-4 points on the real cell. Material that close to a finger, such as a sheet pinched flat between closed pads, is
  not counted either: read a hold from the gripper's width and whether it stalled.
- **Between the jaws.** The ghost also outlines the space between its fingers. That space runs from one finger pad's
  inner face to the other's, is as wide as the pads, and reaches 3 cm up from the tips. Whatever the camera sees
  inside it is coloured pink. `between` says what is there: `{"count", "unit", "gap_mm", "span_fraction",
  "above_tips_mm"}`. Here `span_fraction` is how much of the gap the points cover (in 2 mm bins along the closing
  line), and `above_tips_mm` is their [lowest, highest] height above the fingertips. Zero points means that camera
  sees nothing there that the jaws would close on.
- With no target, the ghost is drawn where the arm is, on top of the real arm when the camera's pose is right. A wrist
  camera moves with its arm, so a ghost far from the arm's present pose is seen from where the camera is now.
- `o.uv(points)` gives the pixels and depths of world points. `o.img` is the RGB image to draw on with cv2 yourself
  (colours are `(r, g, b)`). `o.text(line)` adds a line to the legend.
- `show` writes `views/NAME.png` in the program's run directory (`.robot/runs/<id>/views/`; `.robot/views/` outside a
  run) and replaces the last image of that name. `views/history/` keeps every one. It prints `[view] NAME: PATH` and
  puts a copy on the operator's dashboard. A ghost takes about 30-50 ms.

**3D views.** `viz.View3D` fuses every calibrated camera's depth into one coloured point cloud around a point, and
draws it from virtual cameras you choose, with the same calls (`ghost`, `point`, `points`, `path`, `pose`, `text`):

```python
v = viz.View3D(r, center=T)                    # T: a 4x4 or a point; radius= m framed (default 0.12)
g = v.ghost("left", T, width=0.05)             # body faint, fingers plain, red where it would be inside a surface
v.show("grasp-3d")                             # the default four views in one image
v.show("grasp-3d", views=["jaws", "front", (30, 15)])
```

- Views of the gripper (they need a ghost):
  - `"jaws"` looks through the gap between the fingers, along the gripper's normal: what would be between the jaws.
  - `"along"` looks along the line the jaws close on: the fingertips' heights against the surface.
  - `"approach"` looks down the gripper's axis from behind it.
- Views of the world: `"top"` (the far side up), `"front"` (from +x, facing the arms), `"back"`, `"left"` (from +y),
  `"right"`, `"iso"` (from the front-left, above) and `"iso-right"`.
- Any other view: `(azimuth, elevation)` in degrees, looking at the centre from that direction (azimuth from +x), or
  a camera pose from `viz.look(eye, at)`.
- The default is jaws, along, top and iso about a ghost, and front, left, top and iso without one.
- A level view is a slice: only the points within 4 cm of the centre along the line of sight (2 cm for `"jaws"`), so
  a surface shows as its profile, with height lines every cm.
- A face of the ghost is red when the cameras that see the spot (at least two, when two have a reading) see a
  surface in front of it: it would be inside or under that surface.
- Points between the jaws are pink in every view, and the jaw box is outlined. The ghost's `between` counts them
  over all the cameras together.
- The cloud only has what the cameras see. Surfaces facing away from every camera, and anything they are blocked from,
  are missing. Four views take about 0.3 s.

**Fewer, smaller images.** `viz.show_cameras(name, r, width=960)` shows every camera (or `names=`) as one labelled
grid image; `viz.grid(images, labels, cols=2, width=960)` tiles any images into one. `viz.marks(frame, name,
mask=None, step=40, extra=None, max_marks=60)` puts numbered points on a camera frame (a grid every `step` pixels,
inside `mask` when given, the mask outline's corners first, and `extra` pixels of yours) and returns
`{number: world xyz}`; with a name it shows the image and prints `[marks NAME] 1:(x,y,z) 2:...` (metres).
`on_table=True` keeps only what lies over the table (`viz.table_box(r)`: the arms' fence boxes padded by 10 cm, from
2 cm below z = 0 up), so a colour mask that also catches the floor or a backdrop needs no crop; `within=((x0, x1), (y0,
y1), (z0, z1))` keeps a box of yours; `picture=False` prints the points without the image. `viz.inside(frame, box)` is
the pixel mask behind both.

**Hooks: what you would fetch after a motion, with the motion.** In `python -m robot.kernel`, `kernel.after_motion(fn)`
runs `fn(r, frames)` at the end of every call that moved the arms: `r` is the call's robot, `frames` one grab of every
camera with depth (taken the first time the hook reads it). It runs after the call's code and its `[state]` line,
before its `[views]` line, so what it prints and the images it shows come back in that call's own output.
`kernel.after_call(fn)` runs after every call. Registering a function of the same name again replaces it;
`kernel.remove_hook(name)`, `kernel.hooks()`. A hook that raises prints `[hook NAME] error ...` and the call ends as it
would have; one that takes over a second says so, since every such call pays for it. A mask and its points take
about 0.1 s; a 3D render 0.5-1 s.

```python
def towel(r, frames):
    f = frames["front"]; h = cv2.cvtColor(f.rgb, cv2.COLOR_RGB2HSV)
    viz.marks(f, "towel", mask=(h[..., 0] > 85) & (h[..., 0] < 120) & (h[..., 1] > 90), on_table=True, picture=False)
kernel.after_motion(towel)        # every later call that moves the arms ends with "[marks towel] 1:(x,y,z) ..."
```

**Actions: look at a plan while it runs.** In `python -m robot.kernel`, `kernel.start(fn, name=None, timeout=120)` runs
`fn(r)` (or `fn()`) in the kernel and returns its `Action` at once; `r` is the actions' connection, not closed
when the call ends. Every later call reports it (`[action NAME] running for 3.1 s`, what it printed, and as it ends
`[action NAME] done in 9.8 s`, or stopped, or its error); the call that sees it end prints the arms' `[state]`, shows
every camera as one grid (`views/after-NAME.png`; `views=False`: none) and runs the after-motion hooks. Actions share one
robot connection, kept open from one to the next. `a.stop()` halts every motion (the arms hold) and the action's code goes no further;
`a.wait(timeout=None)` waits for it (True if it ended on its own, without an error); its timeout stops it too. One
action at a time; a call that sends the arms a command stops the running action first. `kernel.action()` is the latest
and `kernel.actions()` lists them.

```python
def grasp(r):
    r.gripper("left", .07); r.move(A, ee="left", duration=3); r.move(G, ee="left", line=True, duration=3)
    r.gripper("left", w - 0.003, speed=0.02, force=30); r.move(L, ee="left", line=True, duration=3)   # w: its width
kernel.start(grasp)               # returns at once; next call: kernel.action().stop(), or .wait(): its output is the look
```

**Pushed action reports (in an episode).** When the harness sets `ROBOT_KERNEL_EVENTS` (a directory), the action makes
its own report as it ends: how it ended, what it printed, the arms' `[state]`, the `after-NAME` grid and the
after-motion hooks (one camera grab shared with them). The harness sends it to you as a message, `[action NAME] ...`
with the images attached, into your running turn or as a new turn if you have ended yours. Nothing waits or polls:
start, look at the plan, then do something else or end your turn. A call that does `a.wait()` gets the report in its
own output instead; other calls only say `[action NAME] done in 9.8 s (its report is sent to you as a message)`.
`EVENTS/actions.json` names the running action, and the episode stays open while one runs.

**The queue: the next action while this one runs.** `kernel.queue(fn, name=None, timeout=120, views=True)` starts `fn` as
the running action ends, or at once if none is running, and returns its `Action`; at most three wait. As an action ends the
next one starts first, and only then is its report made; the report says what started (`[queue] started: B`). An action that
ended with an error or a stop starts nothing: everything queued is dropped (`[queue] dropped: B`) and the arms hold. A check
at the top of `fn` that raises is the same thing. `kernel.queued()` lists what waits, `kernel.flush()` drops it, and
`a.stop()` on a queued action takes it out of the queue. A timeout counts from the action's start.

Every action has a number (`#12`). `kernel.queue(fn, replace_from=12)` takes #12 and everything behind it out of the queue and
puts `fn` (or a list) in their place, in one step; if #12 has started, nothing changes and it raises. `kernel.flush(from_item=12)`
drops #12 and what is behind it. In an episode with a queue, each message carries `[queue]` lines: what runs (`running #14 grasp:
3.1 s in, command 3 (move)`) and what waits, in order; and when your turn ends while an action runs, a `[look N]` message
brings the arms' state, every camera as one grid and those lines.

**Checking the next action from where the queue will leave the arms.** A check made while an action runs sees the arms
where they are now, but the next action's moves are solved when they run, from where the running action ended.
`r.reachable(cands, ee, after=...)`, `r.ik(T, ee, after=...)` and the ghosts (`o.ghost(arm, T, after=...)`,
`View3D.ghost`) take `after={arm: where it will be}`: that arm's joint values, a 4x4 TCP pose, or `{"target": T, "tcp":
..., "free": ...}` as its move was given. IK starts from there (as the move will), and an arm named in `after` is checked
for separation there instead of where it is now. A ghost is still drawn on the latest frame, with the rest of the robot
where it is now; only its IK's starting point changes. `kernel.planned_end()` gives that dict: for each arm, the end of
the last move the running action has sent it so far, unless an action declared its end with `kernel.queue(fn,
ends={arm: pose or joints})` (the latest that says wins); an arm none of them says anything about is left out. It cannot
see moves the running action has yet to send, nor where a queued action without `ends=` goes.

```python
nxt = kernel.planned_end()                                   # {"left": {"target": G, ...}, ...}
out = r.reachable([A2, G2, L2], ee="left", after=nxt)        # as the next action's moves will be solved
kernel.queue(grasp2, ends={"left": L2})                      # the action after it can plan from L2
```

Without `after`, `r.reachable` checks the other arm both where it is commanded now and where its running move ends, so a
goal it would collide with once it gets there is refused at check time (`why`: `separation: ... once right gets where its
running move_to (command 12) ends`); `r.move` refuses it as well. robotd also remembers the IK solutions it finds for
`r.reachable`, `r.ik`, dry runs and moves (a few dozen per arm, keyed by target, `tcp` and `free`). When a move's own solve,
from where the arm is as it starts, misses, the remembered solutions for a target within 1 cm and 0.1 rad are seeds too:
a target `r.reachable` passed near the edge of reach is not refused later because the arm started elsewhere. A solve that
reaches stands, unless a remembered solution is at least 0.5 s quicker to go to (the solve found another branch). The
fence, gripper floor, joint limits and separation apply to whichever solution is chosen.

**What a program prints as it exits.** A program that showed images prints `[views] ["/path/a.png", ...]`, every
path it showed, as one JSON list (`quiet=True` shows are left out; `ROBOT_EXIT_VIEWS=0` turns it off). A program that
sent the arms a command prints `[state] ...` (`State.summary()`): each end effector's position, its gripper's width
and whether it stalled on something or closed on nothing (a close asked to go below the empty-jaw width,
`r.description["gripper_empty_width_m"]`, that ended within 0.5 mm of it; `Result.empty` says the same), contact
where the arms' force estimate is trusted (simulation), a latched fault (`ROBOT_EXIT_STATE=0` turns it off).

**Watching a motion.** `robot.watch.watch(r, arms=None, view_every=None, every=0.25, check=None, signal="watch",
cameras=None, depth=False, lines="changes")` is a with block whose threads (and connections) are its own, so it never
holds up the code inside it. With `view_every=N` it renders, about every N seconds, one compact image of the watched
arms, `views/monitor-K.png`: the wrist and front cameras with each arm's ghost where it is now and its jaw box, and
the point cloud's `jaws` and `along` views around its TCP (about 0.5 s per arm). It prints `[watch view +1.2s] PATH |
left: between the jaws: ... (at the start of the block: 2, so +158)`. `check(state, frames)` or `check(state, frames, between)` runs every `every`
seconds; when it returns a reason, the watcher prints `[watch STOP] reason` and sets the signal to 1, which ends any
motion started with `until=when.signal("watch") > 0`. A state line is printed when a gripper's width, a close on
nothing or (simulation) contact changes (`lines="all"`: every tick; `"none"`: never). The signal is set to 0 as the block starts and ends.

```python
from robot import watch, when
with watch.watch(r, every=0.25, check=lambda st, fr: "closed on nothing" if st.grippers["left"]["width"] < 0.004
                 else None):
    r.move(T_lift, ee="left", duration=3.0, until=when.signal("watch") > 0)
```

## Using libraries

- `r.description["files"]["urdf"]` is both arms in the world frame, written from the driver's own model: a
  `left_tcp` / `right_tcp` link at the tool centre (the point `r.move(T, ee=...)` puts at T) and the driver's joint
  limits, velocity limits and efforts. Load it into cuRobo, PyRoKi or any other URDF library or viewer directly.
- `r.description["arms"]["left"]` is one arm for a per-arm planner: `urdf` (rooted at its base), `base_link`,
  `tcp_link`, `joints`, `finger_joints` (lock them), and `T_world_base` (4x4): a world target T is
  `inv(T_world_base) @ T` in that URDF's frame.
- `r.description["files"]["mjcf"]` is the station's MuJoCo model with the bases where the driver has them (on a real
  cell, where its calibration puts them), in the left base's frame (add y = +0.305 for the world).
- Feed library joint vectors in with their own name lists: `r.move(traj, times=t, joints=names)`. Planning (collision-free paths, constraints beyond `free=`) is the library's job; the robot executes its joint path smoothly and checks it against the joint limits.
- Get the current joints in any order with `r.state().q(names)`.
- Poses are 4x4. `robot.wxyz(T)` and `robot.xyzw(T)` give quaternions in either order. `robot.pose(xyz, rpy=...)` builds one.

## Writing and running a program

Any Python file that uses `robot` runs as usual (`python file.py`). The program runner, `python -m robot run`, runs a
file in a process of its own and adds pauses, a debugger and a record of each run. Such a file lists its steps,
functions `def name(r, v, s)`, in `STEPS`; importing it does no work. `r` is the robot, `v` the vision client (None
when no vision service is configured), and `s` a `SimpleNamespace` kept for the whole run, for what one step hands
the next. It can import modules from its own directory.

```python
def find_cube(r, v, s):
    s.cube = locate(r, "top")                   # a helper from a module next to it
    assert s.cube is not None, "no cube in the top camera"     # a failed assert pauses the run here

def grasp(r, v, s):
    s.g = grasp_at(r, "left", s.cube)

STEPS = [find_cube, grasp, lift]
```

`python -m robot run task.py` starts the program in a process of its own and returns at the first of: it pauses, it
exits, `--wait` seconds pass (default 60). It prints the program's output since the last report, then where and why it
paused, or its exit status and traceback. `python -m robot wait` waits again. `python -m robot pause` pauses the
running program at the next line it runs in your files (a robot request in progress finishes first), then waits as
`wait` does. `python -m robot stop` ends the program, running or paused (`--unattended` too); the arms hold.
Each run has a directory `.robot/runs/<UTC time>/` (`.robot/current` is the latest) with `log.txt` and `status.json`. While a run is alive,
`run` refuses to start another.

| Option | |
|---|---|
| `--break STEP` | pause at the start of that step |
| `--break FILE:LINE` | pause at that line (a pdb breakpoint) |
| `--pause-each-step` | pause after each step |
| `--from STEP`, `--only STEP` | start at that step; run only that step |
| `--unattended` | never pause: a failed `assert` raises `AssertionError`, and any exception ends the program with its traceback and a non-zero exit. For runs nobody watches. |

The program pauses at a failed `assert` in your own files (the program and the modules it imports from its
directory), in that frame and before anything is raised; when any other exception leaves a step (post-mortem); at
`--break`, `--pause-each-step` and `breakpoint()`; and at `python -m robot pause`. Each pause saves `pause-N/` in the
run directory: every camera's rgb (`NAME.png`) and depth (`NAME_depth.png`, 16-bit, mm), their K and T
(`cameras.json`), `r.state()` (`state.json`) and the message. The stops after `n`, `s`, `unt` and `r` save `r.state()`
and the message only.

`python -m robot debug 'CMD'` sends one pdb command to the paused program and prints its output: `p EXPR`, `!STMT`,
`where`, `up`, `down`, `l`, `n`, `s`, `b FILE:LINE`, and the rest of pdb. `r`, `v` and `s` are defined in every
command, whichever frame is selected (after that frame's own names). A command that resumes the program then waits
as `wait` does.

| Command | |
|---|---|
| `c` | go on with the next line. After a failed assert that is the line after it, run as if the check had passed: values computed before your fix stay as they were |
| `reload` | reread your files and `STEPS`; helpers called from then on run the new code, also after `c`. The paused function itself goes on as it was |
| `retry` | reload, then run the current step again from its start; `s` is kept |
| `skip` | go on with the next step |
| `goto STEP` | reload, then go on from that step, also one added since the run started |
| `q` | end the program |

After an exception the step cannot go on: `c`, `n` and `s` are refused; use `retry`, `skip`, `goto` or `q`.

While the program is paused its code stops. Commands it already sent run to their end in the driver, then the arms
hold. In lockstep simulation the world stops too, since nothing steps it; on the real robot and in a real-time
simulation it goes on: a ball in flight or a box on a conveyor has moved on by the time anyone looks, while a
grasp that missed or a key half inserted waits.

What a rerun keeps: `q`, a crash and a driver restart lose `s`, while the world keeps what was done and the files
written stay. When a program ends, crashes or is interrupted, the driver stops the motions it started and the robot
holds.

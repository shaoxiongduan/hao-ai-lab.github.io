# X thread draft: Getting Robot-Use Agents to Run in Real Time

Post from @haoailab. Each post's media file is in this folder. Text between the `---` lines is the post.

Before posting:
- The blog link assumes the post is live at haoailab.com/blogs/realtime-rua/. The main video's end card shows the same address.
- Check the @handles (@AnthropicAI, @OpenAI) and add the authors' handles if they want to be tagged.
- Posts 1, 2, 3, 4 and 7 run 290 to 500 characters, like the lab's recent threads. Anything over 280 needs the account's long-post (Premium) feature.

---
(1/7) Robot-use agents can now control real robots. But they are slow: the arm stands still while the model thinks.

We made the same agent (GPT-6 Astra in @OpenAI Codex) run much closer to real time on a two-arm robot:
- cup task: 667 s → 204 s, 3.3x faster
- towel folding: ~18 min → ~6 min (median)
- robot moving 84% of the time, up from 24%

Blog: https://haoailab.com/blogs/realtime-rua/

Opening clip: @AnthropicAI's Claude Fable 5.2 launch video
---
Media: `01-main-video.mp4`

---
(2/7) Why don't benchmarks show this? In RoboDojo, the simulator waits for the model before it steps. A real robot doesn't wait.

Our early towel-folding runs took 13 to 37 minutes. In one of the longest, the model took 78% of the wall time, and the robot moved for only a quarter of the run.
---
Media: `02-fig4-where-the-time-went.png`

---
(3/7) For astra with low reasoning effort, most of it is per-request overhead, paid on every tool-call round trip.

So we merged round trips:
- each action comes back with the camera views, robot state and the agent's own registered views, so looking costs no extra request
- code runs as soon as it's written; the agent checks its plan while the arm moves, instead of spending an extra turn
- we keep context short, pruning old images into text notes
---
Media: `03-fig11-fewer-requests.png`

---
(4/7) Then we pipelined thinking and motion: the robot moves while the model thinks.

The agent writes actions as Python functions. The robot runs them in order in the background and reports back as each action ends, while the model plans the next steps or rewrites the plan.

Pipelining removes no model time, but it hides 137 of the 182 s behind motion.
---
Media: `04-pipelining.png`

---
(5/7) We first gave Astra a cup game: three cups hide a pear, a ball and nothing, and it has to put the pear under the empty cup (video at 3.5x).
---
Media: `05-cup-game-3.5x.mp4`

---
(6/7) Then something harder: folding a crumpled towel (video at 8x).

In both runs, most of the model's time was hidden behind the robot's motion, and the robot stood still only 16% and 22% of the time.
---
Media: `06-crumpled-towel-8x.mp4`

---
(7/7) However, hiding the model's time behind motion doesn't make the robot react fast. Each action is still based on what the robot saw about 5 s earlier, so it needs about 5 s to react when something changes.

We also treated Codex and Astra as a black box. With open models served for robots, the server and the harness can be designed together, leaving much more room to cut model time and be even faster.

Blog: https://haoailab.com/blogs/realtime-rua/

By Shaoxiong Duan, Yang Yuanbo, Junda Chen, Yulun Wu and Hao Zhang
---
Media: none

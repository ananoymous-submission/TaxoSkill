---
title: ScienceWorld OpenEnv
emoji: 🔬
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 8000
license: apache-2.0
tags:
  - rl-environment
pinned: false
---

# ScienceWorld OpenEnv

A typed, stateful [OpenEnv](https://github.com/huggingface/OpenEnv) environment for [ScienceWorld](https://github.com/allenai/ScienceWorld).

Each WebSocket connection owns one complete ScienceWorld episode:

```text
connect -> reset(task_id) -> step(action) -> ... -> close
```

The public demo initially permits one active session. Concurrent-session support remains disabled until real Java-process isolation and capacity tests pass.

The generic web UI's argument-free **Reset** button deterministically opens task `0`. Typed clients should pass `task_id` explicitly to select another task.

## Typed client

```python
from scienceworld_env.client import ScienceWorldClient
from scienceworld_env.models import ScienceWorldAction

async with ScienceWorldClient(base_url="https://your-hf-user-scienceworld-openenv.hf.space") as env:
    initial = await env.reset(task_id=0)
    result = await env.step(ScienceWorldAction(command="look around"))
```

## Task catalog

The image contains one canonical catalog with 1,888 frozen task identities:

- Development: 1,483
- Test-Seen: 194
- Test-Unseen: 211

Official task classes are retained as private catalog metadata and are not exposed in public observations.

## Licensing and attribution

ScienceWorld is distributed under Apache-2.0. This environment uses `scienceworld==1.2.3` and preserves the benchmark source revision in its frozen task manifests.

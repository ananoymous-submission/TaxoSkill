---
title: ALFWorld OpenEnv
emoji: 🏠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 8000
license: mit
tags:
  - rl-environment
pinned: false
---

# ALFWorld OpenEnv

A typed, stateful OpenEnv environment for the text-only ALFWorld benchmark.

Each WebSocket connection owns one complete episode:

```text
connect -> reset(task_id) -> step(action) -> ... -> close
```

The canonical catalog uses the logical splits `development`, `test_seen`, and `test_unseen`. The upstream runtime directory remains named `train` internally because frozen ALFWorld gamefile identities contain that path.

The manifest-referenced runtime assets are stored as a checksum-pinned compressed archive in the Space repository and extracted into the image at build time. Containers start with the exact local ALFWorld data already available.

The deployment initially permits one active session. Capacity is increased only after real session-isolation and cleanup tests pass.

The generic web UI's argument-free Reset button opens development task `191`. Typed clients should always pass `task_id` explicitly.

## Runtime assets

The embedded archive contains exactly the upstream assets referenced by the canonical catalog:

- `logic/`
- `json_2.1.1/train/` for the logical development pool
- `json_2.1.1/valid_seen/`
- `json_2.1.1/valid_unseen/`

`valid_train/` is excluded because no canonical task manifest references it.

## Licensing and attribution

ALFWorld is distributed under the MIT license. The environment uses the text-only ALFWorld runtime and preserves the released `json_2.1.1` source provenance in its frozen task manifests.

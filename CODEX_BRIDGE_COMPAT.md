# Codex Module Bridge v1 compatibility

Bastion Lunchbox Fixes v1.0.4 and Codex Module Bridge v1 both publish `mods/codex/gun_calibration` (`0x9537023f38d32bcd`). A mod manager can deploy only one winning implementation of that resource.

v1.0.4 makes the Bastion implementation a functional superset of the supplied Bridge v1 dispatcher. Before the unchanged Bastion v13-derived runtime starts, it conditionally loads:

- `mods/codex/p11_self_heal`
- `mods/codex/constitution_bolt_amr`

Each lookup is guarded with `stingray.Application.can_get('lua', name)` and each `require` is isolated with `pcall`. The `CodexModuleBridge` global guard prevents duplicate compatibility initialization.

## Required priority

Users can keep both mods installed independently, but **Bastion Lunchbox Fixes must win the `gun_calibration` collision**. With Arsenal's normal priority behavior, place Bastion Lunchbox Fixes after/below Codex Module Bridge v1, then Purge / Deploy.

Bingus Shared Loader remains required and should follow its own current priority instructions.

## Scope

This shim is intentionally pinned to the supplied **Codex Module Bridge v1** behavior. A later bridge version that changes its module list or startup logic must be revalidated before claiming compatibility.

HUD Ballistic Trajectory Overlay v2 remains incompatible with this implementation because it also owns `gun_calibration` and contains additional gameplay behavior not reproduced here.

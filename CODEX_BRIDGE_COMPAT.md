# Codex Module Bridge v1 compatibility

Bastion Lunchbox Fixes v1.0.5 preserves the compatibility dispatcher introduced in v1.0.4. Bastion Lunchbox Fixes and Codex Module Bridge v1 both publish `mods/codex/gun_calibration` (`0x9537023f38d32bcd`), so only one implementation of that resource can win after deployment.

## Codex Module Bridge is optional

Bastion Lunchbox Fixes does **not** require Codex Module Bridge to be installed.

When Bastion wins `gun_calibration`, its compatibility prefix conditionally checks for and starts these separately installed Codex modules if they exist:

- `mods/codex/p11_self_heal`
- `mods/codex/constitution_bolt_amr`

Each lookup is guarded with `stingray.Application.can_get('lua', name)` and each `require` is isolated with `pcall`. Missing Codex modules are treated as not installed, not as a fatal dependency failure. The `CodexModuleBridge` global guard prevents duplicate compatibility initialization.

## Required priority when Codex Module Bridge is installed

Users can keep both mods installed independently, but **Bastion Lunchbox Fixes must win the `gun_calibration` collision**. With Arsenal's normal priority behavior, place Bastion Lunchbox Fixes after/below Codex Module Bridge v1, then Purge / Deploy.

Bingus Shared Loader remains required and should follow its own current priority instructions.

## Scope

This shim is intentionally pinned to the supplied **Codex Module Bridge v1** behavior. A later bridge version that changes its module list or startup logic must be revalidated before claiming compatibility.

HUD Ballistic Trajectory Overlay v2 remains incompatible with this implementation because it also owns `gun_calibration` and contains additional gameplay behavior not reproduced here.

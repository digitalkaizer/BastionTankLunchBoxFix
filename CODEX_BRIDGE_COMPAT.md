# Codex Module Bridge v1 compatibility

Bastion Lunchbox Fixes v1.0.6 and Codex Module Bridge v1 both publish `mods/codex/gun_calibration` (`0x9537023f38d32bcd`), so only one implementation of that resource can win after deployment.

## Codex Module Bridge is optional

Bastion Lunchbox Fixes does **not** require Codex Module Bridge to be installed.

If a real `CodexModuleBridge` global is already active, the DigitalKaizer compatibility dispatcher skips its own module dispatch. Otherwise it checks for and conditionally loads:

- `mods/codex/p11_self_heal`
- `mods/codex/constitution_bolt_amr`

Each lookup uses `stingray.Application.can_get('lua', name)` and each `require` is isolated with `pcall`.

## Ownership

v1.0.6 no longer claims third-party runtime/log identities. The compatibility shim uses:

- `_G.DigitalKaizerBastionCodexCompat`
- `DigitalKaizerBastionLunchboxFixCompat.log`

It does **not** create `_G.CodexModuleBridge` and does **not** write `CodexModuleBridge.log`.

## Priority when Codex Module Bridge is installed

Keep both mods independently installed, but **Bastion Lunchbox Fixes must win the `gun_calibration` collision**. With Arsenal's normal priority behavior, place Bastion Lunchbox Fixes after/below Codex Module Bridge v1, then Purge / Deploy.

Bingus Shared Loader remains required.

HUD Ballistic Trajectory Overlay v2 remains incompatible because it also requires its own implementation of `mods/codex/gun_calibration`.

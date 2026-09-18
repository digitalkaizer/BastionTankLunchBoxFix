# Changelog

## v1.0.4 — Codex Module Bridge v1 Compatibility

- Preserves the exact known-working v13 Bastion runtime core used by v1.0.3.
- Corrects the Bastion runtime/log revision label to `runtime-v13-options-v1.0.4`; this is metadata only and does not change locator/writer behavior.
- Adds a small compatibility dispatcher before the Bastion runtime for **Codex Module Bridge v1**.
- When Bastion Lunchbox Fix has winning priority for `mods/codex/gun_calibration`, it now conditionally starts the two modules Bridge v1 was responsible for starting:
  - `mods/codex/p11_self_heal`
  - `mods/codex/constitution_bolt_amr`
- Uses `stingray.Application.can_get('lua', name)` before `require(name)`, so either Codex gameplay module may be absent without breaking the Bastion fix.
- Uses the `CodexModuleBridge` global guard to avoid duplicate compatibility initialization.
- Users may keep Codex Module Bridge v1 installed independently; Arsenal may still report the shared `gun_calibration` resource collision. **Bastion Lunchbox Fix must win that collision.**
- This compatibility behavior is pinned specifically to Bridge v1 and should be revalidated if that mod changes its module list or startup behavior.
- HUD Ballistic Trajectory Overlay v2 remains incompatible because it also requires its own implementation of `mods/codex/gun_calibration`.

## v1.0.3 — Exact v13 Core

- Rebased the mod runtime directly on the known-working `Bastion_Fix_Main_Health_HUD_Runtime_v13_Arsenal.zip` patch core.
- Preserved v13's Bastion signature, exact zone hashes/HP validation, serialized layout constants, targeted locator, `large_ro_fallback`, protected writer, verification, rollback, and retry logic.
- Removed the unrelated experimental Main Health HUD from the v13 source.
- Added only three option gates to v13's proven `plan()` write list:
  - Lunch Boxes → 0% Main Health transfer
  - Lunch Boxes → AV4
  - Side Skirts → 0% Main Health transfer
- Retained all eight mutually exclusive Arsenal configurations.
- Replaced the repository builder so it packages the exact-v13-derived runtime template instead of reconstructing the runtime layout.

## v1.0.0–v1.0.2 — Superseded experimental builds

These builds used a reconstructed runtime layout/locator rather than the exact known-working v13 implementation. Testing showed the rewritten locator could repeatedly return zero candidates and fail to apply the patch. They are superseded by v1.0.3 and later.

# Changelog

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

These builds used a reconstructed runtime layout/locator rather than the exact known-working v13 implementation. Testing showed the rewritten locator could repeatedly return zero candidates and fail to apply the patch. They are superseded by v1.0.3.

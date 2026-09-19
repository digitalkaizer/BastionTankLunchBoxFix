# Changelog

## v1.0.6 — Staged Skirt Fix + DigitalKaizer Ownership

- Ships the user-tested staged-write fix for **Light Lunch Boxes + Side Skirts 0% Main**.
- Confirmed by testing:
  - **All 3 Fixes** loads successfully.
  - **Light Lunch Boxes 0% Main Only** loads successfully.
  - Directly writing 0% Side Skirts while Lunch Boxes stay AV2 causes an immediate CTD.
  - Temporarily staging Lunch Boxes AV2→AV4, applying the skirt writes, then restoring AV4→AV2 loads successfully.
- The final gameplay state for option 2 is still **AV2 Lunch Boxes + 0% Main-transfer Side Skirts**; AV4 exists only during the patch transaction.
- The staged sequence is now part of the common runtime and is gated only by `OPT_SKIRTS_TRANSFER and not OPT_HEAVY_ARMOR`.
- Retains rollback behavior: if staging restoration fails, completed skirt writes are rolled back rather than leaving a mixed state.
- Keeps all three variants at identical generated Lua/archive geometry.
- Moves runtime ownership to DigitalKaizer identifiers:
  - global: `DigitalKaizerBastionLunchboxFix`
  - log: `DigitalKaizerBastionLunchboxFix.log`
  - compatibility global: `DigitalKaizerBastionCodexCompat`
  - compatibility log: `DigitalKaizerBastionLunchboxFixCompat.log`
- The compatibility shim no longer creates the third-party `CodexModuleBridge` global or writes `CodexModuleBridge.log`.
- Codex Module Bridge remains optional and independently installed.

## v1.0.5 — Configuration / Archive Stability Cleanup

- Reduced the configuration list to three useful choices.
- Standardized generated Lua/archive geometry across variants.
- Testing subsequently proved archive geometry was not the cause of the remaining option-2 CTD.

## v1.0.4 — Codex Module Bridge v1 Compatibility

- Added conditional compatibility dispatch for the two known Codex Bridge v1 modules.
- Preserved the exact-v13 Bastion locator/protected writer.

## v1.0.3 — Exact v13 Core

- Rebased the runtime directly on the known-working v13 patch core.

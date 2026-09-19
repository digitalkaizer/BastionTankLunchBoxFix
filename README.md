# Bastion Lunchbox Fixes v1.0.6

A focused runtime bugfix/tweak package for the **TD-220 Bastion MK XVI**, targeting the external stowage boxes ("Lunch Boxes") and side skirts.

## Configurations

1. **All 3 Fixes (Recommended)** — Lunch Boxes 0% Main + AV4; Side Skirts 0% Main.
2. **Light Lunch Boxes + Side Skirts 0% Main** — Lunch Boxes remain AV2; Lunch Boxes and Side Skirts use 0% Main transfer.
3. **Light Lunch Boxes 0% Main Only** — Lunch Boxes remain AV2 with 0% Main transfer; Side Skirts remain vanilla.

## v1.0.6 staged-write fix

Testing isolated the remaining CTD to write sequencing.

The final state **AV2 Lunch Boxes + 0% Side Skirts** is valid, but directly writing the skirt Main-transfer fields while the Lunch Boxes remain AV2 causes an immediate CTD during load.

For configuration 2, v1.0.6 therefore performs this transaction:

`Lunch Boxes AV2 → AV4` → `apply 0% skirt writes` → `Lunch Boxes AV4 → AV2`

The AV4 state is temporary and exists only during the patch transaction. Before control returns to the game, the Lunch Boxes are restored to AV2. Failure handling restores staged armor and rolls back completed gameplay writes rather than intentionally leaving a mixed state.

Configurations 1 and 3 continue through the same common runtime without invoking that staging path.

## Runtime basis

The locator/writer remains derived from the known-working v13 runtime:

- exact Bastion header/hash/HP validation
- `ZONE0 = 520`, `STRIDE = 552`
- `ARMOR = 216`, `HEALTH = 232`, `MAIN = 248`
- `TARGET_REGION_SIZE = 35590144`
- `TARGET_OFFSET = 0x994006`
- `VirtualQuery` / `ReadProcessMemory`
- temporary `VirtualProtect` to RW
- `WriteProcessMemory`
- immediate protection restoration
- write verification, rollback, and post-write validation

## DigitalKaizer runtime ownership

v1.0.6 uses project-owned runtime/log identities:

- `_G.DigitalKaizerBastionLunchboxFix`
- `DigitalKaizerBastionLunchboxFix.log`
- `_G.DigitalKaizerBastionCodexCompat`
- `DigitalKaizerBastionLunchboxFixCompat.log`

The legacy `KZR_BastionAccessoryArmor` global is checked only as a duplicate-load guard for older builds; v1.0.6 does not create it.

## Codex Module Bridge compatibility

**Codex Module Bridge is optional.**

Both mods publish `mods/codex/gun_calibration`. If Codex Module Bridge v1 is installed, Bastion Lunchbox Fixes must win that resource collision.

The compatibility dispatcher no longer impersonates the external mod: it does not create `_G.CodexModuleBridge` or write `CodexModuleBridge.log`. If a real bridge is already active, the dispatcher skips its own work. Otherwise it conditionally loads the two known Bridge v1 gameplay modules if they are present.

## Requirement

**Bingus Shared Loader by CowboyBingus is required and is not included.**

## Installation

1. Install Bingus Shared Loader.
2. Import `Bastion_Lunchbox_Fixes_v1.0.6_ExactV13_Arsenal.zip` into Arsenal.
3. Choose one configuration.
4. If Codex Module Bridge v1 is installed, keep it independent and give Bastion Lunchbox Fixes winning priority for `mods/codex/gun_calibration`.
5. Purge/deploy with the game closed.
6. Launch Helldivers 2.

## Logs

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\DigitalKaizerBastionLunchboxFix.log`

Compatibility dispatch:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\DigitalKaizerBastionLunchboxFixCompat.log`

## Disclaimer

Experimental third-party mod built from community research, game-data analysis, reverse engineering, in-game testing, and AI-assisted code generation. Helldivers 2 is property of Arrowhead Game Studios / Sony Interactive Entertainment.

# Bastion Lunchbox Fixes v1.0.5

A focused runtime bugfix/tweak package for the **TD-220 Bastion MK XVI**, targeting the external stowage boxes ("Lunch Boxes") and side skirts.

> **v1.0.5 stability cleanup:** the proven v1.0.4 / exact-v13 Bastion runtime and Codex Module Bridge compatibility dispatcher are preserved. The option list is reduced to three useful configurations, and all generated variants are forced to use identical Lua-resource and Stingray-archive geometry.

## Features

- **Lunch Boxes — 0% Main Health transfer:** the six external stowage zones (6–11) remain destructible, but damage to them does not transfer into the Bastion's Main Health pool.
- **Lunch Boxes — AV2 → AV4:** the recommended configuration changes those six zones from Armor Value 2 to Armor Value 4 without changing their HP/durability.
- **Side Skirts — 0% Main Health transfer:** the eight side-skirt zones (16–23) remain destructible with their existing AV4/HP, but damage to the skirts does not transfer into Main Health.

## Configurations

Only three configurations remain:

1. **All 3 Fixes (Recommended)** — Lunch Boxes 0% Main + AV4; Side Skirts 0% Main.
2. **Light Lunch Boxes + Side Skirts 0% Main** — Lunch Boxes remain AV2; Lunch Boxes and Side Skirts use 0% Main transfer.
3. **Light Lunch Boxes 0% Main Only** — Lunch Boxes remain AV2 with 0% Main transfer; Side Skirts remain vanilla.

The old heavy-only, skirt-only, diagnostic, and redundant combination choices have been removed.

## v1.0.5 non-default crash mitigation

Testing reported that every v1.0.4 configuration except the recommended first option could crash to desktop during load.

The leading structural difference in the package was that the old builder substituted variable-width Lua values and labels into each option. For example, `true` is four bytes while `false` is five bytes. That meant the embedded Lua resource and final Stingray archive were not the same size between configurations.

v1.0.5 removes that difference without changing the proven locator/writer core:

- enabled values still use `true`;
- disabled values use the Lua falsey literal `nil `, which is also exactly four bytes;
- runtime configuration labels are padded to a fixed 25-byte width;
- the builder aborts unless all three variants have identical Lua size, archive size, and resource data offset.

The recommended option keeps the same gameplay/runtime substitutions it used previously. This change is intentionally concentrated in packaging/configuration generation rather than the proven Bastion memory locator and protected writer.

## Why the recommended fix matters

The stock Bastion's external parts interact badly with Helldivers 2's overpenetration mechanic.

When a projectile's Armor Penetration is at least two levels above the Armor Value of the part it hits, the projectile can continue through that part and strike another damageable part behind it. The continuing projectile typically retains roughly 70% of its ballistic damage.

Dangerous Automaton weapons such as Cannon Turrets and Rocket Striders use AP6 attacks, while stock Lunch Boxes are AV2. Raising the Lunch Boxes to AV4 in the recommended configuration prevents the most extreme AP gap while the 0% Main-transfer changes stop those sacrificial external parts from directly draining Main Health.

## Runtime basis

The Bastion patch remains based directly on the uploaded, known-working v13 patch core rather than a reconstructed FileDiver layout.

Preserved runtime behavior/constants include:

- `BASTION_HEADER` signature validation
- 14 exact zone hashes and expected HP values
- `ZONE0 = 520`
- `STRIDE = 552`
- `ZONE_HASH = 96`
- `ARMOR = 216`
- `HEALTH = 232`
- `MAIN = 248`
- `TARGET_REGION_SIZE = 35590144`
- `TARGET_OFFSET = 0x994006`
- exact-size locator plus `large_ro_fallback`
- `VirtualQuery` / `ReadProcessMemory`
- `VirtualProtect` / `WriteProcessMemory`
- write verification and page-protection restoration
- rollback and post-write validation
- `START_TICK = 600`
- `RETRY_INTERVAL = 300`
- `MAX_ATTEMPTS = 16`

## Codex Module Bridge v1 compatibility

**Codex Module Bridge is not required by this mod.**

Codex Module Bridge v1 and Bastion Lunchbox Fixes both publish:

`mods/codex/gun_calibration`

The compatibility behavior introduced in v1.0.4 is preserved. When Bastion wins that shared resource, its small dispatcher checks whether these separately installed Codex modules exist before trying to load them:

- `mods/codex/p11_self_heal`
- `mods/codex/constitution_bolt_amr`

The checks use `stingray.Application.can_get('lua', name)` and protected `require` calls. If those modules or Codex Module Bridge are not installed, Bastion continues without requiring them.

If **Codex Module Bridge v1 is installed**, keep it as an independent mod and give **Bastion Lunchbox Fixes the winning priority** for `mods/codex/gun_calibration`. Under Arsenal's normal priority behavior, place Bastion Lunchbox Fixes after/below Codex Module Bridge v1 while still following Bingus Shared Loader's own placement instructions.

Compatibility remains pinned specifically to the supplied Codex Module Bridge v1 behavior. **HUD Ballistic Trajectory Overlay v2 remains incompatible** because it also requires its own implementation of `mods/codex/gun_calibration`.

## Requirement: Bingus Shared Loader

**Bingus Shared Loader by CowboyBingus is required and is not included.** Install it separately and follow the loader's current installation/load-order instructions.

Codex Module Bridge is optional and is not bundled.

## Installation

1. Install **Bingus Shared Loader** separately.
2. Import `Bastion_Lunchbox_Fixes_v1.0.5_ExactV13_Arsenal.zip` into Arsenal.
3. Choose one **Fix Configuration** option.
4. Use **All 3 Fixes (Recommended)** for the intended complete setup.
5. If using **Codex Module Bridge v1**, leave it independently installed and give Bastion Lunchbox Fixes winning priority for their shared `gun_calibration` resource.
6. Purge/deploy the Arsenal profile with the game closed.
7. Launch Helldivers 2.

The Bastion runtime writes diagnostic status to:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\BastionAccessoryArmor.log`

The compatibility dispatcher also attempts to write:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\CodexModuleBridge.log`

## Repository layout

- `src/CodexModuleBridgeCompat.lua` — optional Bridge v1 compatibility dispatcher
- `src/BastionLunchboxFixes.template.part*.lua` — exact-v13-derived Bastion runtime template
- `manifest.json` — Arsenal option definitions
- `BUILD_INFO.json` — preserved constants, compatibility contract, and derivation details
- `build_bastion_lunchbox_fixes.py` — builds and validates equal-geometry Arsenal variants
- `CHANGELOG.md` — release/history notes

## Disclaimer

**Vibe coded with ChatGPT.**

This is an experimental third-party mod built from community research, game-data analysis, reverse engineering, in-game testing, and AI-assisted code generation. Compatibility with future Helldivers 2, Codex Module Bridge, or Shared Loader versions is not guaranteed. Use at your own risk.

Helldivers 2 is property of Arrowhead Game Studios / Sony Interactive Entertainment. This project is not affiliated with or endorsed by Arrowhead, Sony, CowboyBingus, or the Codex Module Bridge author.

# Bastion Lunchbox Fixes v1.0.3

A focused runtime bugfix/tweak package for the **TD-220 Bastion MK XVI**, targeting the external stowage boxes ("Lunch Boxes") and side skirts.

> **v1.0.3 correction:** the runtime is now derived directly from the known-working `Bastion_Fix_Main_Health_HUD_Runtime_v13_Arsenal.zip` patch core. The v13 locator, validation, protected writer, retry behavior, and rollback logic are preserved. The three requested fixes are only gated behind Arsenal configuration options; the unrelated experimental Main Health HUD is not included.

## Features

- **Lunch Boxes — 0% Main Health transfer:** the six external stowage zones (6–11) remain destructible, but damage to them no longer transfers into the Bastion's Main Health pool.
- **Lunch Boxes — AV2 → AV4:** optionally changes those six zones from Armor Value 2 to Armor Value 4 without changing their HP/durability.
- **Side Skirts — 0% Main Health transfer:** the eight side-skirt zones (16–23) remain destructible with their existing AV4/HP, but damage to the skirts no longer transfers into Main Health.

All eight possible combinations are included as one mutually exclusive **Fix Configuration** option group. **All 3 Fixes (Recommended)** enables the intended complete setup.

## Why this fix matters

The stock Bastion's external parts interact badly with Helldivers 2's lesser-known **overpenetration** mechanic.

When a projectile's Armor Penetration is at least two levels above the Armor Value of the part it hits, the projectile can continue through that part and strike another damageable part behind it. The continuing projectile typically deals about **30% reduced damage**, retaining roughly **70% of its ballistic damage**.

That creates a damage "double dip" against the Bastion. Dangerous Automaton weapons such as **Cannon Turrets and Rocket Striders use AP6 attacks**, while the stock Lunch Boxes are only **AV2**.

Using only the ballistic portion of a Cannon Turret projectile as an example:

- Initial ballistic damage: **1,500**
- A stock Lunch Box hit can transfer damage into Bastion Main Health.
- AP6 greatly exceeds AV2, so the projectile can overpenetrate the Lunch Box and continue into another tank zone.
- The overpenetrating hit retains roughly 70% damage: **1,500 × 0.70 = 1,050** additional ballistic damage.
- This can produce as much as **2,550 ballistic damage worth of interaction from one projectile path** before considering other damage components.

This example intentionally does **not** include the Cannon Turret projectile's separate **AP4 explosive damage**.

With the recommended configuration, the Lunch Boxes become **AV4**, and both Lunch Boxes and side skirts transfer **0%** of their damage into Main Health. They remain destructible external components but behave more like sacrificial armor/stowage rather than amplified structural weak points.

## v1.0.3 runtime basis

v1.0.3 is based directly on the uploaded, known-working v13 patch core rather than a reconstructed FileDiver layout.

The following v13 behavior/constants are preserved:

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

The only gameplay-code change is inside the proven v13 `plan()` function: its existing writes are gated by the three selected options.

## Configurations

1. **All 3 Fixes (Recommended)** — Lunch Boxes 0% Main + AV4; Side Skirts 0% Main
2. **Lunch Heavy Armor + Side Skirts 0% Main**
3. **Lunch 0% Main + Heavy Armor**
4. **Lunch 0% Main + Side Skirts 0% Main**
5. **Lunch Boxes Heavy Armor Only**
6. **Lunch Boxes 0% Main Only**
7. **Side Skirts 0% Main Only**
8. **All Off / Diagnostic** — runs the v13 locator/validator with no gameplay writes

## Requirement: Bingus Shared Loader

**Bingus Shared Loader by CowboyBingus is REQUIRED and is not included.** Install it separately and follow the loader's current installation/load-order instructions.

This is an unofficial third-party integration. It is not authored, maintained, endorsed, or supported by CowboyBingus.

### Compatibility warning

This experimental build currently uses the loader registration resource associated with `mods/codex/gun_calibration`. That resource is also used by **HUD Ballistic Trajectory Overlay v2**. Do **not** run both mods together with this implementation; a resource collision can prevent one from loading.

## Installation

1. Install **Bingus Shared Loader** separately.
2. Import `Bastion_Lunchbox_Fixes_v1.0.3_ExactV13_Arsenal.zip` into Arsenal.
3. Enable **Bastion Lunchbox Fixes**.
4. Choose one **Fix Configuration** option.
5. Use **All 3 Fixes (Recommended)** for the full intended setup.
6. Purge/deploy the Arsenal profile with the game closed.
7. Launch Helldivers 2.

The exact-v13-derived runtime writes its diagnostic status to:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\BastionAccessoryArmor.log`

## Repository layout

- `src/BastionLunchboxFixes.template.part*.lua` — the exact-v13-derived runtime template split into three source parts for repository storage; the builder concatenates them verbatim before substituting the three option booleans/configuration label
- `manifest.json` — Arsenal option definitions
- `BUILD_INFO.json` — preserved v13 constants, source hash, and derivation details
- `build_bastion_lunchbox_fixes.py` — substitutes option values and packages the resulting Lua into the Arsenal archive format
- `CHANGELOG.md` — release/history notes

## Disclaimer

**Vibe coded with ChatGPT.**

This is an experimental third-party mod built from community research, game-data analysis, reverse engineering, in-game testing, and AI-assisted code generation. Compatibility with future Helldivers 2 or Shared Loader versions is not guaranteed. Use at your own risk.

Bingus Shared Loader is authored and distributed separately by CowboyBingus; none of its code is bundled here.

Helldivers 2 is property of Arrowhead Game Studios / Sony Interactive Entertainment. This project is not affiliated with or endorsed by Arrowhead, Sony, or CowboyBingus.

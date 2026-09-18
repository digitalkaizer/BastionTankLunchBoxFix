# Bastion Lunchbox Fixes v1.0.0

A focused runtime bugfix/tweak package for the TD-220 Bastion MK XVI.

## Features

- **“Lunch Boxes” — No Longer Transfer Damage to Main**: forces Bastion stowage/lunch-box zones 6–11 to 0% Main Health transfer. On the currently tested game data these zones already appear to be configured for 0% transfer; this option is included as an explicit runtime enforcement/test toggle.
- **Lunch Boxes — Light to Heavy Armor**: changes zones 6–11 from Armor Value 2 to Armor Value 4. Health/durability is not changed.
- **Side Skirts — No Longer Transfer Damage to Main**: forces zones 16–23 from 100% Main Health transfer to 0% while leaving their HP/durability and armor unchanged.

Because the shared loader exposes one runtime module entry rather than composable feature hooks, this package ships all eight possible combinations as a single Arsenal radio-choice group. Select **All 3 Fixes (Recommended)** unless you specifically want to isolate/test one behavior.

## Requirement: Bingus Shared Loader

**Bingus Shared Loader by CowboyBingus is REQUIRED and is NOT included in this archive.** Install it separately and follow CowboyBingus's current load-order instructions for the loader.

This is an **unofficial third-party mod** using the Shared Loader runtime. It is not authored, maintained, endorsed, or supported by CowboyBingus.

### Important compatibility warning

This experimental release currently uses the loader's registered `mods/codex/gun_calibration` module slot because that is a loader entry point proven to work with this runtime patch. That slot is also used by **HUD Ballistic Trajectory Overlay v2**. **Do not run Bastion Lunchbox Fixes and HUD Ballistic Trajectory Overlay v2 together.** Whichever resource wins the load-order conflict can prevent the other from loading.

A future Shared Loader change that gives this mod its own third-party module registration would remove that specific limitation.

## How it works

The runtime searches for the current Bastion HealthComponent data layout in memory and validates several known Bastion fields before touching anything. For enabled fixes it temporarily changes protection only on the individual 4-byte data fields being edited, writes and verifies the value, then restores the original page protection.

If the expected Bastion structure cannot be validated, the mod stops without intentionally applying the requested writes. This is meant to reduce the chance of writing to the wrong data after a game update; it is not a guarantee of compatibility or safety.

Diagnostic log:
`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\BastionLunchboxFixes.log`

## Installation (Arsenal)

1. Install **Bingus Shared Loader** separately.
2. Import `Bastion_Lunchbox_Fixes_v1.0.0_Arsenal.zip` into Arsenal.
3. Enable the mod in your profile.
4. Open its Options and enable **Fix Configuration**.
5. Choose one configuration. **All 3 Fixes (Recommended)** is the intended full bugfix setup.
6. Place/deploy Bingus Shared Loader according to CowboyBingus's current loader instructions, then deploy the profile.
7. Launch the game and check `BastionLunchboxFixes.log` if you need to confirm what applied.

## Disclaimer

**Vibe coded with ChatGPT.**

This is an experimental third-party mod built from community research, runtime testing, reverse-engineered game data, and AI-assisted code generation. Compatibility with future Helldivers 2 updates, other runtime mods, or future versions of Bingus Shared Loader is **not guaranteed**.

Use at your own risk. Back out the mod first if you encounter crashes, unexpected Bastion behavior, or conflicts after a game/loader update.

Bingus Shared Loader is the work of CowboyBingus and is distributed separately. This package does not redistribute the Shared Loader.

Helldivers 2 is property of Arrowhead Game Studios / Sony Interactive Entertainment. This project is not affiliated with or endorsed by Arrowhead, Sony, or CowboyBingus.

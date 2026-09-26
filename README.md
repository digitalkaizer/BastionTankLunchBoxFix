# HD2 Better Tanks v1.0.0

A configurable overhaul for the TD-220 Bastion and TD-110 Storm/Maelstrom tanks.

## Requirements

- Helldivers 2
- Bingus Shared Loader v15+ / API 1
- Arsenal-compatible mod loader/installer

## Configuration

The master configuration is:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Config\digitalKaizer-BetterTanks.ini`

The mod creates the config on first run if it is missing. Restart Helldivers 2 after changing settings unless noted otherwise in the config.

The shipped config contains the default Better Tanks balance preset. Each option documents the original game value where known, so users can tune or restore individual settings themselves.

## Features

- Bastion and Storm main health
- Constitution and destruction countdown behavior
- Configurable frontal, stowage, side-skirt, and additional structural armor zones
- Main-health damage transfer by armor-zone group
- Explosive damage taken
- Acceleration and handling parameters
- Five experimental tracked-vehicle coefficients
- Bastion cannon ammunition, HMG ammunition, fire rates, and cannon reload time
- Storm Gatling belt size, spare belts, fire rate, and reload time
- Storm smoke capacity and delay
- Storm rear-missile capacity
- Bastion and Storm stratagem cooldowns
- Optional integrated tank HUD that follows configured health and ammunition values

## Installation

Install the archive through Arsenal and enable **Core - Better Tanks**.

The **Integrated Tank HUD** option is optional. Do not enable another tank HUD that replaces the same runtime data at the same time.

## Log

Runtime information is written to:

`%LOCALAPPDATA%\CowboyBingus\Helldivers2\Logs\HD2BetterTanks.log`

## Compatibility

Do not simultaneously use other mods that edit the same tank health, armor, handling, ammunition, weapon timing, smoke, missile-capacity, cooldown, or HUD data.

## v1.0.0 hotfix

The current v1.0.0 build fixes the remaining Bastion HMG HUD validation limit so custom HMG capacities above the vanilla 2000-round value are correctly picked up by the integrated Tank HUD.

## Notes

Some tracked-vehicle fields are still not fully understood. The config identifies those settings conservatively rather than assigning unsupported names to them.

A third-party license notice is included where legally required.

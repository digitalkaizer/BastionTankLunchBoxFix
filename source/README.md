# HD2 Better Tanks v1.0.0 source

The v1.0.0 base source archive is stored here as six split Base64 parts.

Run:

```bash
python rebuild_source_archive.py
```

This reconstructs:

`HD2_Better_Tanks_v1.0.0_Source.tar.xz`

Base archive SHA-256:

`503f8a2f9f0b70ce62f950532a5ffffc851b9be616c62ed759039c77c87d8da7`

## Current v1.0.0 hotfix

The current Better Tanks v1.0.0 release includes the Bastion HMG HUD capacity fix in:

`HMG_HUD_hotfix.patch`

After extracting the reconstructed source archive, apply it from the extracted source directory with:

```bash
patch -p1 < ../HMG_HUD_hotfix.patch
```

The fix removes the remaining hard-coded 2000-round Bastion HMG HUD validation limit and uses the configured `BT.bastion_hmg_ammo` value instead.

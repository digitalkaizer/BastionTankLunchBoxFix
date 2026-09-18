"""Reproducibly build Bastion Lunchbox Fixes v1.0.3.

The runtime template is derived directly from the known-working v13 patch core.
The builder only substitutes the three option booleans/configuration label and
packages the resulting Lua verbatim into the Stingray archive.
"""

from pathlib import Path
import shutil
import struct
import zipfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "build"
ARCHIVE_NAME = "9ba626afa44a3aa3.patch_0"
RESOURCE_TYPE = 0xA14E8DFA2CD117E2
RESOURCE_HASH = 0x9537023F38D32BCD
TEMPLATE_PARTS = [
    ROOT / "src" / "BastionLunchboxFixes.template.part1.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part2.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part3.lua",
]

VARIANTS = [
    ("01_All_3_Fixes", "All 3 Fixes (Recommended)", True, True, True),
    ("02_Lunch_Heavy_Skirts", "Lunch Heavy Armor + Side Skirts 0% Main", False, True, True),
    ("03_Lunch_0Main_Heavy", "Lunch 0% Main + Heavy Armor", True, True, False),
    ("04_Lunch_0Main_Skirts", "Lunch 0% Main + Side Skirts 0% Main", True, False, True),
    ("05_Lunch_Heavy_Only", "Lunch Boxes Heavy Armor Only", False, True, False),
    ("06_Lunch_0Main_Only", "Lunch Boxes 0% Main Only", True, False, False),
    ("07_Skirts_0Main_Only", "Side Skirts 0% Main Only", False, False, True),
    ("08_All_Off", "All Off / Diagnostic", False, False, False),
]


def lua_source(label: str, lunch_0main: bool, lunch_heavy: bool, skirts_0main: bool) -> bytes:
    text = "".join(path.read_text(encoding="utf-8") for path in TEMPLATE_PARTS)
    values = {
        "{{OPT_LUNCH_TRANSFER}}": str(lunch_0main).lower(),
        "{{OPT_HEAVY_ARMOR}}": str(lunch_heavy).lower(),
        "{{OPT_SKIRTS_TRANSFER}}": str(skirts_0main).lower(),
        "{{CONFIG_LABEL}}": label.replace("'", "\\'"),
    }
    for token, value in values.items():
        text = text.replace(token, value)
    if "{{" in text or "}}" in text:
        raise RuntimeError("Unresolved template token")
    return text.encode("utf-8")


def make_archive(lua: bytes) -> bytes:
    resource = struct.pack("<II", len(lua), 2) + lua
    count = 1
    data_offset = (104 + 80 * count + 15) & ~15
    final_size = (data_offset + len(resource) + 15) & ~15
    body = bytearray(final_size)
    header = struct.pack("<III20sQQ24s", 0xF0000011, 1, count, b"", final_size, 0, b"")
    types = struct.pack("<IIQIIII", 0, 0, RESOURCE_TYPE, count, 0, 16, 16)
    entry = struct.pack(
        "<7Q6I", RESOURCE_HASH, RESOURCE_TYPE, data_offset,
        0, 0, 0, 0, len(resource), 0, 0, 16, 16, 0
    )
    body[:104 + len(entry)] = header + types + entry
    body[data_offset:data_offset + len(resource)] = resource
    return bytes(body)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy2(ROOT / "manifest.json", OUT / "manifest.json")

    for folder, label, lunch_0main, lunch_heavy, skirts_0main in VARIANTS:
        dest = OUT / folder
        dest.mkdir(parents=True)
        lua = lua_source(label, lunch_0main, lunch_heavy, skirts_0main)
        (dest / ARCHIVE_NAME).write_bytes(make_archive(lua))
        (dest / f"{ARCHIVE_NAME}.stream").write_bytes(b"")
        (dest / f"{ARCHIVE_NAME}.gpu_resources").write_bytes(b"")

    arsenal = ROOT / "Bastion_Lunchbox_Fixes_v1.0.3_ExactV13_Arsenal.zip"
    with zipfile.ZipFile(arsenal, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(OUT.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(OUT))
    print(arsenal)


if __name__ == "__main__":
    main()

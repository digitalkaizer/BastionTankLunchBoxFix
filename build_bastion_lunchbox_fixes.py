"""Reproducibly build Bastion Lunchbox Fixes v1.0.5.

The Bastion runtime template remains derived directly from the known-working v13
patch core. v1.0.5 prepends the compatibility dispatcher for Codex Module
Bridge v1 plus the separately packaged vehicle aggro diagnostic, then substitutes
only the three Bastion option booleans/config label and packages the combined Lua
source into the existing gun_calibration resource.
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
RELEASE_VERSION = "1.0.5"
EXPECTED_BRIDGE_MODULES = (
    "mods/codex/p11_self_heal",
    "mods/codex/constitution_bolt_amr",
    "mods/codex/vehicle_aggro_diagnostic",
)

TEMPLATE_PARTS = [
    ROOT / "src" / "CodexModuleBridgeCompat.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part1.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part2.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part3.lua",
]

VARIANTS = [
    ("01_All_3_Fixes", "All 3 Fixes (Recommended)", True, True, True),
    ("02_Lunch_Heavy_Skirts", "Lunch Heavy Armor + Side Skirts 0% Main", False, True, True),
    ("03_Lunch_0Main_Heavy", "Lunch 0% Main + Heavy Armor", True, True, False),
    ("04_Lunch_0Main_Skirts", "Lunch 0% Main + Side Skirts 0% Main", True, False, True),
    ("05_Lunch_Heavy_Only", "Lunch Boxes Heavy Armor Only", False, False, False),
    ("06_Lunch_0Main_Only", "Lunch Boxes 0% Main Only", True, False, False),
    ("07_Skirts_0Main_Only", "Side Skirt 0% Main Only", False, False, True),
    ("08_All_Off", "All Off / Diagnostic", False, False, False),
]

# Preserve v1.0.4 variant semantics exactly.
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

    bastion_guard = "if rawget(_G, 'KZR_BastionAccessoryArmor') then return end"
    bridge_guard = "if not rawget(_G, 'CodexModuleBridge') then"
    if bridge_guard not in text or bastion_guard not in text:
        raise RuntimeError("Expected compatibility/runtime guards are missing")
    if text.index(bridge_guard) > text.index(bastion_guard):
        raise RuntimeError("Codex bridge compatibility must precede Bastion initialization")
    for module_name in EXPECTED_BRIDGE_MODULES:
        if module_name not in text:
            raise RuntimeError(f"Missing compatibility module: {module_name}")

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


def verify_archive(archive: bytes, expected_lua: bytes) -> None:
    if len(archive) < 184:
        raise RuntimeError("Archive is unexpectedly small")
    magic, version, count = struct.unpack_from("<III", archive, 0)
    if magic != 0xF0000011 or version != 1 or count != 1:
        raise RuntimeError("Unexpected Stingray archive header")

    resource_hash, resource_type, data_offset = struct.unpack_from("<QQQ", archive, 104)
    if resource_hash != RESOURCE_HASH or resource_type != RESOURCE_TYPE:
        raise RuntimeError("Archive resource identity mismatch")

    lua_size, lua_kind = struct.unpack_from("<II", archive, data_offset)
    if lua_kind != 2:
        raise RuntimeError("Unexpected Lua resource kind")
    embedded = archive[data_offset + 8:data_offset + 8 + lua_size]
    if embedded != expected_lua:
        raise RuntimeError("Embedded Lua does not match generated source")


def deterministic_zip(root: Path, destination: Path) -> None:
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            zf.writestr(info, path.read_bytes())


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy2(ROOT / "manifest.json", OUT / "manifest.json")

    for folder, label, lunch_0main, lunch_heavy, skirts_0main in VARIANTS:
        dest = OUT / folder
        dest.mkdir(parents=True)
        lua = lua_source(label, lunch_0main, lunch_heavy, skirts_0main)
        archive = make_archive(lua)
        verify_archive(archive, lua)
        (dest / ARCHIVE_NAME).write_bytes(archive)
        (dest / f"{ARCHIVE_NAME}.stream").write_bytes(b"")
        (dest / f"{ARCHIVE_NAME}.gpu_resources").write_bytes(b"")

    arsenal = ROOT / f"Bastion_Lunchbox_Fixes_v{RELEASE_VERSION}_ExactV13_Arsenal.zip"
    deterministic_zip(OUT, arsenal)
    print(arsenal)


if __name__ == "__main__":
    main()

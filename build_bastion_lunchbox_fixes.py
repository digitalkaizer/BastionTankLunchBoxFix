"""Reproducibly build DigitalKaizer Bastion Lunchbox Fixes v1.0.6.

v1.0.6 preserves the exact-v13 Bastion locator/protected writer and the optional
Codex Module Bridge v1 compatibility behavior, permanently incorporates the
proven staged-write sequence required by the AV2 Lunch Boxes + 0% Side Skirts
configuration, and uses DigitalKaizer-owned runtime/log identifiers.

All variants use the same Lua source geometry; only fixed-width option literals
and a fixed-width configuration label differ.
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
RELEASE_VERSION = "1.0.6"
RUNTIME_LABEL_WIDTH = 25
EXPECTED_BRIDGE_MODULES = (
    "mods/codex/p11_self_heal",
    "mods/codex/constitution_bolt_amr",
)

TEMPLATE_PARTS = [
    ROOT / "src" / "CodexModuleBridgeCompat.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part1.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part2.lua",
    ROOT / "src" / "BastionLunchboxFixes.template.part3.lua",
]

# folder, Arsenal label, fixed-width runtime label, lunch 0% Main, lunch AV4, skirts 0% Main
VARIANTS = [
    (
        "01_All_3_Fixes",
        "All 3 Fixes (Recommended)",
        "All 3 Fixes (Recommended)",
        True, True, True,
    ),
    (
        "02_Light_Lunch_And_Skirts",
        "Light Lunch Boxes + Side Skirts 0% Main",
        "Light Boxes + 0% Skirts",
        True, False, True,
    ),
    (
        "03_Light_Lunch_Only",
        "Light Lunch Boxes 0% Main Only",
        "Light Boxes Only",
        True, False, False,
    ),
]


def fixed_bool(value: bool) -> str:
    """Return a four-byte Lua truthy/falsey literal."""
    return "true" if value else "nil "


def fixed_label(label: str) -> str:
    if len(label) > RUNTIME_LABEL_WIDTH:
        raise RuntimeError(f"Runtime label too long ({len(label)} > {RUNTIME_LABEL_WIDTH}): {label}")
    return label.ljust(RUNTIME_LABEL_WIDTH)


def lua_source(runtime_label: str, lunch_0main: bool, lunch_heavy: bool, skirts_0main: bool) -> bytes:
    text = "".join(path.read_text(encoding="utf-8") for path in TEMPLATE_PARTS)
    values = {
        "{{OPT_LUNCH_TRANSFER}}": fixed_bool(lunch_0main),
        "{{OPT_HEAVY_ARMOR}}": fixed_bool(lunch_heavy),
        "{{OPT_SKIRTS_TRANSFER}}": fixed_bool(skirts_0main),
        "{{CONFIG_LABEL}}": fixed_label(runtime_label).replace("'", "\\'"),
    }
    for token, value in values.items():
        text = text.replace(token, value)
    if "{{" in text or "}}" in text:
        raise RuntimeError("Unresolved template token")

    bastion_guard = "if rawget(_G, 'DigitalKaizerBastionLunchboxFix')"
    compat_guard = "if not rawget(_G, 'DigitalKaizerBastionCodexCompat') then"
    if compat_guard not in text or bastion_guard not in text:
        raise RuntimeError("Expected DigitalKaizer compatibility/runtime guards are missing")
    if text.index(compat_guard) > text.index(bastion_guard):
        raise RuntimeError("Codex compatibility must precede Bastion initialization")
    for module_name in EXPECTED_BRIDGE_MODULES:
        if module_name not in text:
            raise RuntimeError(f"Missing Codex Bridge v1 module: {module_name}")

    if "logger.open_log('DigitalKaizerBastionLunchboxFix.log')" not in text:
        raise RuntimeError("Owned Bastion log path is missing")
    if "logger.open_log('DigitalKaizerBastionLunchboxFixCompat.log')" not in text:
        raise RuntimeError("Owned compatibility log path is missing")
    if "rawset(_G, 'CodexModuleBridge'" in text:
        raise RuntimeError("Compatibility shim must not claim the CodexModuleBridge global")

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

    reference_lua_size = None
    reference_archive_size = None
    reference_data_offset = None

    for folder, label, runtime_label, lunch_0main, lunch_heavy, skirts_0main in VARIANTS:
        dest = OUT / folder
        dest.mkdir(parents=True)
        lua = lua_source(runtime_label, lunch_0main, lunch_heavy, skirts_0main)
        archive = make_archive(lua)
        verify_archive(archive, lua)

        data_offset = struct.unpack_from("<Q", archive, 120)[0]
        if reference_lua_size is None:
            reference_lua_size = len(lua)
            reference_archive_size = len(archive)
            reference_data_offset = data_offset
        else:
            if len(lua) != reference_lua_size:
                raise RuntimeError(
                    f"Variant {label!r} changed Lua size: {len(lua)} != {reference_lua_size}"
                )
            if len(archive) != reference_archive_size:
                raise RuntimeError(
                    f"Variant {label!r} changed archive size: {len(archive)} != {reference_archive_size}"
                )
            if data_offset != reference_data_offset:
                raise RuntimeError(
                    f"Variant {label!r} changed resource data offset: {data_offset} != {reference_data_offset}"
                )

        (dest / ARCHIVE_NAME).write_bytes(archive)
        (dest / f"{ARCHIVE_NAME}.stream").write_bytes(b"")
        (dest / f"{ARCHIVE_NAME}.gpu_resources").write_bytes(b"")

    arsenal = ROOT / f"Bastion_Lunchbox_Fixes_v{RELEASE_VERSION}_ExactV13_Arsenal.zip"
    deterministic_zip(OUT, arsenal)
    print(arsenal)
    print(
        f"Verified {len(VARIANTS)} variants: lua_size={reference_lua_size}, "
        f"archive_size={reference_archive_size}, data_offset={reference_data_offset}"
    )


if __name__ == "__main__":
    main()

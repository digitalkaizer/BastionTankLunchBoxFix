from pathlib import Path
import json
import shutil
import struct
import uuid
import zipfile

OUT = Path('/mnt/data/Bastion_Lunchbox_Fixes_build')
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(parents=True)

ARCHIVE_NAME = '9ba626afa44a3aa3.patch_0'
TYPE = 0xA14E8DFA2CD117E2
MODULE_PATH = 'mods/codex/gun_calibration'
GUID = '1eb0b075-035c-49d8-b7f0-67311d56b83b'


def resource_hash(name):
    data = name.encode('utf-8')
    mask, mix = (1 << 64) - 1, 0xC6A4A7935BD1E995
    value = len(data) * mix & mask
    end = len(data) // 8 * 8
    for (word,) in struct.iter_unpack('<Q', data[:end]):
        word = word * mix & mask
        word ^= word >> 47
        value = (value ^ (word * mix & mask)) * mix & mask
    if data[end:]:
        value = (value ^ int.from_bytes(data[end:], 'little')) * mix & mask
    value ^= value >> 47
    value = value * mix & mask
    return value ^ (value >> 47)


def make_archive(resources):
    count = len(resources)
    offset = (104 + 80 * count + 15) & ~15
    entries, body = bytearray(), bytearray(offset)
    for index, (name, resource) in enumerate(sorted(resources.items())):
        entries += struct.pack('<7Q6I', name, TYPE, offset, 0, 0, 0, 0,
                               len(resource), 0, 0, 16, 16, index)
        body += resource
        body += b'\0' * (-len(body) % 16)
        offset = len(body)
    header = struct.pack('<III20sQQ24s', 0xF0000011, 1, count, b'', offset, 0, b'')
    types = struct.pack('<IIQIIII', 0, 0, TYPE, count, 0, 16, 16)
    body[:104 + len(entries)] = header + types + entries
    return bytes(body)


def lua_source(lunch_transfer, heavy_armor, skirts_transfer, label):
    return f'''-- Bastion Lunchbox Fixes v1.0.0
-- Third-party module for Bingus Shared Loader API 1.
-- Configuration: {label}

local OPT_LUNCH_TRANSFER = {str(lunch_transfer).lower()}
local OPT_HEAVY_ARMOR = {str(heavy_armor).lower()}
local OPT_SKIRTS_TRANSFER = {str(skirts_transfer).lower()}

local ffi = require('ffi')
ffi.cdef [[
typedef unsigned int DWORD;
typedef unsigned long long SIZE_T;
typedef int BOOL;
typedef struct _MEMORY_BASIC_INFORMATION_BLF {{
    void *BaseAddress;
    void *AllocationBase;
    DWORD AllocationProtect;
    DWORD Alignment1;
    SIZE_T RegionSize;
    DWORD State;
    DWORD Protect;
    DWORD Type;
    DWORD Alignment2;
}} MEMORY_BASIC_INFORMATION_BLF;
SIZE_T VirtualQuery(const void *lpAddress, MEMORY_BASIC_INFORMATION_BLF *lpBuffer, SIZE_T dwLength);
BOOL VirtualProtect(void *lpAddress, SIZE_T dwSize, DWORD flNewProtect, DWORD *lpflOldProtect);
]]

local kernel32 = ffi.load('kernel32')
local loader = rawget(_G, 'CowboyBingusModLoader')
local lines = {{}}
local function note(s) lines[#lines + 1] = tostring(s) end
local function flush()
    pcall(function()
        local f = loader and loader.open_log and loader.open_log('BastionLunchboxFixes.log') or nil
        if not f then return end
        for i = 1, #lines do f:write(lines[i], '\\n') end
        f:close()
    end)
end

note('Bastion Lunchbox Fixes v1.0.0')
note('Third-party Bingus Shared Loader module; API 1')
note('Configuration: {label}')
note('Lunch Boxes 0% Main=' .. tostring(OPT_LUNCH_TRANSFER) .. '; Lunch Boxes Heavy Armor=' .. tostring(OPT_HEAVY_ARMOR) .. '; Side Skirts 0% Main=' .. tostring(OPT_SKIRTS_TRANSFER))

local PAGE_READONLY = 0x02
local PAGE_READWRITE = 0x04
local MEM_COMMIT = 0x1000
local MEM_PRIVATE = 0x20000
local EXPECTED_REGION_SIZE = 35590144 -- 0x21F1000
local BASTION_REGION_OFFSET = 0x994000
local BASTION_COMPONENT_IN_REGION = 6

-- Current DamageableZone layout (FileDiver/current game data):
local DEFAULT_ZONE_INFO_SIZE = 424
local HEALTH_HEADER_SIZE = 64
local ZONE_BASE = HEALTH_HEADER_SIZE + DEFAULT_ZONE_INFO_SIZE -- 488
local ZONE_STRIDE = 520
local OFF_ARMOR = 212
local OFF_HEALTH = 228
local OFF_AFFECTS_MAIN = 244

local function p8(addr) return ffi.cast('uint8_t*', addr) end
local function read_u32(addr) return tonumber(ffi.cast('uint32_t*', p8(addr))[0]) end
local function read_i32(addr) return tonumber(ffi.cast('int32_t*', p8(addr))[0]) end
local function read_f32(addr) return tonumber(ffi.cast('float*', p8(addr))[0]) end
local function near(a, b) return math.abs(a - b) < 0.0001 end
local function zone_addr(component, index) return component + ZONE_BASE + index * ZONE_STRIDE end

local function validate_component(c)
    if read_i32(c + 0) ~= 8000 then return false, 'main_health' end
    if read_u32(c + 16) ~= 1 then return false, 'regen_segments' end
    if read_i32(c + 24) ~= 70000 then return false, 'constitution' end
    if not near(read_f32(c + 28), -10000.0) then return false, 'constitution_rate' end
    if read_u32(c + 40) ~= 2 then return false, 'unit_size' end
    if not near(read_f32(c + 52), 2.0) then return false, 'wounded_sway' end
    if not near(read_f32(c + 56), 0.75) then return false, 'wounded_move' end

    for i = 6, 11 do
        local z = zone_addr(c, i)
        local armor = read_u32(z + OFF_ARMOR)
        local hp = read_i32(z + OFF_HEALTH)
        local main = read_f32(z + OFF_AFFECTS_MAIN)
        if armor ~= 2 and armor ~= 4 then return false, 'lunch_armor_' .. i end
        if hp <= 0 or hp > 1000 then return false, 'lunch_hp_' .. i end
        if not near(main, 0.0) and not near(main, 1.0) then return false, 'lunch_main_' .. i end
    end
    for i = 16, 23 do
        local z = zone_addr(c, i)
        local armor = read_u32(z + OFF_ARMOR)
        local hp = read_i32(z + OFF_HEALTH)
        local main = read_f32(z + OFF_AFFECTS_MAIN)
        if armor ~= 4 then return false, 'skirt_armor_' .. i end
        if hp <= 0 or hp > 5000 then return false, 'skirt_hp_' .. i end
        if not near(main, 0.0) and not near(main, 1.0) then return false, 'skirt_main_' .. i end
    end
    return true, 'ok'
end

local function find_bastion()
    local mbi = ffi.new('MEMORY_BASIC_INFORMATION_BLF[1]')
    local address = 0
    local max_address = 0x00007FFFFFFF0000
    local candidates = 0
    while address < max_address do
        local got = kernel32.VirtualQuery(ffi.cast('const void*', address), mbi, ffi.sizeof(mbi[0]))
        if got == 0 then break end
        local base = tonumber(ffi.cast('uintptr_t', mbi[0].BaseAddress))
        local alloc = tonumber(ffi.cast('uintptr_t', mbi[0].AllocationBase))
        local size = tonumber(mbi[0].RegionSize)
        if size <= 0 then break end

        if tonumber(mbi[0].State) == MEM_COMMIT and tonumber(mbi[0].Type) == MEM_PRIVATE and
           tonumber(mbi[0].Protect) == PAGE_READONLY and size == EXPECTED_REGION_SIZE and
           alloc ~= 0 and (base - alloc) == BASTION_REGION_OFFSET then
            candidates = candidates + 1
            local c = base + BASTION_COMPONENT_IN_REGION
            local ok, why = validate_component(c)
            if ok then return c, base, alloc, candidates, 'validated' end
            note('Rejected candidate at ' .. tostring(c) .. ': ' .. tostring(why))
        end

        local next_address = base + size
        if next_address <= address then break end
        address = next_address
    end
    return nil, nil, nil, candidates, 'not_found'
end

local writes, already = 0, 0
local function protected_write_u32(addr, value)
    local current = read_u32(addr)
    if current == value then already = already + 1; return true end
    local old = ffi.new('DWORD[1]')
    if kernel32.VirtualProtect(ffi.cast('void*', addr), 4, PAGE_READWRITE, old) == 0 then
        return false, 'VirtualProtect(RW) failed'
    end
    ffi.cast('uint32_t*', p8(addr))[0] = value
    local verified = read_u32(addr) == value
    local ignored = ffi.new('DWORD[1]')
    kernel32.VirtualProtect(ffi.cast('void*', addr), 4, old[0], ignored)
    if not verified then return false, 'verify failed' end
    writes = writes + 1
    return true
end

local function protected_write_f32(addr, value)
    local current = read_f32(addr)
    if near(current, value) then already = already + 1; return true end
    local old = ffi.new('DWORD[1]')
    if kernel32.VirtualProtect(ffi.cast('void*', addr), 4, PAGE_READWRITE, old) == 0 then
        return false, 'VirtualProtect(RW) failed'
    end
    ffi.cast('float*', p8(addr))[0] = value
    local verified = near(read_f32(addr), value)
    local ignored = ffi.new('DWORD[1]')
    kernel32.VirtualProtect(ffi.cast('void*', addr), 4, old[0], ignored)
    if not verified then return false, 'verify failed' end
    writes = writes + 1
    return true
end

local function apply()
    local component, region, alloc, candidates, status = find_bastion()
    if not component then
        note('STOPPED: Bastion HealthComponent not found/validated; candidates=' .. tostring(candidates))
        return false
    end
    note('Validated Bastion HealthComponent=' .. tostring(component) .. '; region=' .. tostring(region) .. '; allocation=' .. tostring(alloc))

    if OPT_LUNCH_TRANSFER then
        for i = 6, 11 do
            local ok, err = protected_write_f32(zone_addr(component, i) + OFF_AFFECTS_MAIN, 0.0)
            if not ok then note('STOPPED: lunch transfer zone ' .. i .. ': ' .. tostring(err)); return false end
        end
    end
    if OPT_HEAVY_ARMOR then
        for i = 6, 11 do
            local ok, err = protected_write_u32(zone_addr(component, i) + OFF_ARMOR, 4)
            if not ok then note('STOPPED: lunch armor zone ' .. i .. ': ' .. tostring(err)); return false end
        end
    end
    if OPT_SKIRTS_TRANSFER then
        for i = 16, 23 do
            local ok, err = protected_write_f32(zone_addr(component, i) + OFF_AFFECTS_MAIN, 0.0)
            if not ok then note('STOPPED: skirt transfer zone ' .. i .. ': ' .. tostring(err)); return false end
        end
    end

    local ok, why = validate_component(component)
    if not ok then note('WARNING: post-write validation failed: ' .. tostring(why)); return false end
    note('APPLIED: writes=' .. tostring(writes) .. '; already_correct=' .. tostring(already) .. '; HP/durability unchanged')
    if OPT_LUNCH_TRANSFER then note('Lunch Boxes zones 6-11: Main Health transfer forced to 0%') end
    if OPT_HEAVY_ARMOR then note('Lunch Boxes zones 6-11: Armor forced to AV4 (Heavy)') end
    if OPT_SKIRTS_TRANSFER then note('Side Skirts zones 16-23: Main Health transfer forced to 0%') end
    if not OPT_LUNCH_TRANSFER and not OPT_HEAVY_ARMOR and not OPT_SKIRTS_TRANSFER then note('No gameplay changes selected (All Off diagnostic variant).') end
    return true
end

local ok, result = pcall(apply)
if not ok then
    note('ERROR: ' .. tostring(result))
    flush()
    error(result)
end
flush()
return result
'''

variants = [
    ('01_All_3_Fixes', 'All 3 Fixes (Recommended)', True, True, True,
     'Lunch Boxes: 0% Main transfer + Heavy Armor; Side Skirts: 0% Main transfer.'),
    ('02_Lunch_Heavy_Skirts', 'Lunch Heavy Armor + Side Skirts 0% Main', False, True, True,
     'Heavy Lunch Boxes and non-transfering Side Skirts; does not explicitly enforce Lunch Box Main transfer.'),
    ('03_Lunch_0Main_Heavy', 'Lunch 0% Main + Heavy Armor', True, True, False,
     'Both Lunch Box fixes; Side Skirts remain vanilla.'),
    ('04_Lunch_0Main_Skirts', 'Lunch 0% Main + Side Skirts 0% Main', True, False, True,
     'Stops Main Health transfer from Lunch Boxes and Side Skirts; Lunch Box armor remains vanilla.'),
    ('05_Lunch_Heavy_Only', 'Lunch Boxes Heavy Armor Only', False, True, False,
     'Changes Lunch Boxes from light armor (AV2) to heavy armor (AV4) only.'),
    ('06_Lunch_0Main_Only', 'Lunch Boxes 0% Main Only', True, False, False,
     'Explicitly forces Lunch Box Main Health transfer to 0% only.'),
    ('07_Skirts_0Main_Only', 'Side Skirts 0% Main Only', False, False, True,
     'Stops Side Skirt damage from transferring to Bastion Main Health only.'),
    ('08_All_Off', 'All Off / Diagnostic', False, False, False,
     'Loads and validates the runtime module but makes no gameplay changes.'),
]

for folder, label, a, b, c, desc in variants:
    d = OUT / folder
    d.mkdir()
    src = lua_source(a,b,c,label).encode('utf-8')
    resource = struct.pack('<II', len(src), 2) + src
    archive = make_archive({resource_hash(MODULE_PATH): resource})
    (d / ARCHIVE_NAME).write_bytes(archive)
    (d / (ARCHIVE_NAME + '.stream')).write_bytes(b'')
    (d / (ARCHIVE_NAME + '.gpu_resources')).write_bytes(b'')

manifest_desc = (
    'Bastion tank accessory bugfixes with selectable configurations. '
    'Requires Bingus Shared Loader (installed separately). Unofficial third-party integration; '
    'compatibility is not guaranteed. Current experimental build uses the loader registration slot '
    'also used by HUD Ballistic Trajectory Overlay v2, so do not use both together.'
)
manifest = {
    'Version': 1,
    'Guid': GUID,
    'Name': 'Bastion Lunchbox Fixes',
    'Description': manifest_desc,
    'Options': [{
        'Name': 'Fix Configuration',
        'Description': 'Choose one Bastion Lunchbox Fixes configuration. All 3 Fixes is recommended.',
        'SubOptions': [
            {'Name': label, 'Description': desc, 'Include': [folder]}
            for folder, label, a,b,c,desc in variants
        ]
    }]
}
(OUT/'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')

readme = '''# Bastion Lunchbox Fixes v1.0.0

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
`%LOCALAPPDATA%\\CowboyBingus\\Helldivers2\\Logs\\BastionLunchboxFixes.log`

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
'''
(OUT/'README.md').write_text(readme, encoding='utf-8')

build_info = {
    'name':'Bastion Lunchbox Fixes',
    'version':'1.0.0',
    'module_resource': MODULE_PATH,
    'module_resource_hash': f'{resource_hash(MODULE_PATH):016x}',
    'archive_name': ARCHIVE_NAME,
    'damageable_zone': {
        'zone_stride_bytes':520,
        'armor_offset_bytes':212,
        'health_offset_bytes':228,
        'affects_main_health_offset_bytes':244,
        'default_zone_info_bytes':424,
        'damageable_zones_offset_in_health_component_bytes':488,
        'lunch_box_zones':'6-11',
        'side_skirt_zones':'16-23'
    },
    'runtime_locator': {
        'allocation_region_offset_hex':'0x994000',
        'component_offset_from_region_bytes':6,
        'expected_region_size_bytes':35590144
    },
    'compatibility_warning':'Uses mods/codex/gun_calibration loader slot; conflicts with HUD Ballistic Trajectory Overlay v2.',
    'variants': [{'folder':f,'name':n,'lunch_0main':a,'lunch_heavy':b,'skirts_0main':c} for f,n,a,b,c,d in variants]
}
(OUT/'BUILD_INFO.json').write_text(json.dumps(build_info, indent=2)+'\n', encoding='utf-8')

release = Path('/mnt/data/Bastion_Lunchbox_Fixes_v1.0.0_Arsenal.zip')
if release.exists(): release.unlink()
with zipfile.ZipFile(release,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for file in sorted(OUT.rglob('*')):
        if file.is_file():
            z.write(file, file.relative_to(OUT).as_posix())

srcdir = Path('/mnt/data/Bastion_Lunchbox_Fixes_Source_v1.0.0')
if srcdir.exists(): shutil.rmtree(srcdir)
srcdir.mkdir()
shutil.copy(__file__, srcdir/'build_bastion_lunchbox_fixes.py')
for folder, label, a,b,c,desc in variants:
    (srcdir/(folder + '.lua')).write_text(lua_source(a,b,c,label), encoding='utf-8')
shutil.copy(OUT/'BUILD_INFO.json', srcdir/'BUILD_INFO.json')
shutil.copy(OUT/'README.md', srcdir/'README.md')
source_zip = Path('/mnt/data/Bastion_Lunchbox_Fixes_v1.0.0_Source.zip')
if source_zip.exists(): source_zip.unlink()
with zipfile.ZipFile(source_zip,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for file in sorted(srcdir.rglob('*')):
        if file.is_file(): z.write(file, file.relative_to(srcdir).as_posix())

print(release)
print(source_zip)
print('guid', GUID)
print('module_hash', f'{resource_hash(MODULE_PATH):016x}')

-- Bastion Lunchbox Fixes v1.0.3 - exact v13 patch core + option gates
--
-- Derived directly from the known-working Bastion runtime v13 patch core.
-- The locator, validation hashes/offsets, memory scan, protected writer,
-- retry timing, verification, and rollback behavior remain v13.
-- Only the write plan is gated by Arsenal-selected booleans.
--
-- v10 keeps the exact targeted DataLibrary locator proven by v9.
-- v9 then proved direct WriteProcessMemory cannot write this allocation:
-- Windows returned ERROR_NOACCESS (998) with zero bytes written.
--
-- v10 therefore temporarily changes ONLY the memory page containing each
-- already-validated 4-byte target field from PAGE_READONLY to PAGE_READWRITE,
-- performs and verifies the write, then restores the exact original protection
-- immediately. It never changes executable/image pages and never leaves a page
-- writable intentionally.

if rawget(_G, 'KZR_BastionAccessoryArmor') then return end

local OPT_LUNCH_TRANSFER = {{OPT_LUNCH_TRANSFER}}
local OPT_HEAVY_ARMOR = {{OPT_HEAVY_ARMOR}}
local OPT_SKIRTS_TRANSFER = {{OPT_SKIRTS_TRANSFER}}
local CONFIG_LABEL = '{{CONFIG_LABEL}}'


local state = {
    revision = 'runtime-v13-options-v1.0.3',
    active = false,
    done = false,
    copies = 0,
    writes = 0,
    status = 'installed; exact v13 targeted DataLibrary locator + protected data writer armed'
}
rawset(_G, 'KZR_BastionAccessoryArmor', state)

local function report(message)
    state.status = tostring(message)
    print('[BastionAccessoryArmor] ' .. state.revision .. ': ' .. state.status)
    pcall(function()
        local logger = rawget(_G, 'CowboyBingusModLoader')
        local file = logger and logger.open_log and logger.open_log('BastionAccessoryArmor.log')
        if not file then return end
        file:write('Bastion Accessory Armor ' .. state.revision .. '\n')
        file:write(state.status .. '\n')
        file:write('copies=' .. tostring(state.copies) .. '\n')
        file:write('writes=' .. tostring(state.writes) .. '\n')
        file:close()
    end)
end

local ffi = require('ffi')
ffi.cdef [[
    void *GetCurrentProcess(void);
    void *GetModuleHandleA(const char *name);
    int ReadProcessMemory(void *process, const void *address, void *buffer, size_t size, size_t *read);
    int WriteProcessMemory(void *process, void *address, const void *buffer, size_t size, size_t *written);
    int VirtualProtect(void *address, size_t size, uint32_t new_protection, uint32_t *old_protection);
    typedef struct {
        void *base; void *allocation_base; uint32_t allocation_protection;
        uint16_t partition; uint16_t reserved; size_t size;
        uint32_t state; uint32_t protection; uint32_t type;
    } KzrBastionMemoryRegionV8;
    size_t VirtualQuery(const void *address, void *region, size_t size);
    uint32_t GetLastError(void);
]]

local kernel = ffi.load('kernel32')
local process = kernel.GetCurrentProcess()
local query_region = ffi.cast('size_t (*)(const void *, void *, size_t)', kernel.VirtualQuery)

local function address_number(address)
    return tonumber(ffi.cast('uintptr_t', address))
end

local function read_memory(address, size)
    if size <= 0 then return '' end
    local buffer = ffi.new('uint8_t[?]', size)
    local count = ffi.new('size_t[1]')
    if kernel.ReadProcessMemory(process, address, buffer, size, count) == 0 then return nil end
    if tonumber(count[0]) ~= size then return nil end
    return ffi.string(buffer, size)
end

local function u32(bytes, offset)
    offset = offset or 0
    local a,b,c,d = bytes:byte(offset + 1, offset + 4)
    if not d then return nil end
    return a + b*256 + c*65536 + d*16777216
end

local function page_info(address)
    local region = ffi.new('KzrBastionMemoryRegionV8[1]')
    if query_region(address, region, ffi.sizeof(region[0])) ~= ffi.sizeof(region[0]) then return nil end
    return {
        state=tonumber(region[0].state),
        type=tonumber(region[0].type),
        protection=tonumber(region[0].protection),
        base=address_number(region[0].base),
        size=tonumber(region[0].size),
        allocation=address_number(region[0].allocation_base)
    }
end

local function patchable_private_data(address, size)
    if size <= 0 then return false, 'invalid_size' end
    local cursor = ffi.cast('uint8_t *', address)
    local remaining = size
    while remaining > 0 do
        local info = page_info(cursor)
        if not info then return false, 'VirtualQuery_failed' end
        if info.state ~= 0x1000 or info.type ~= 0x20000
            or (info.protection ~= 0x02 and info.protection ~= 0x04) then
            return false, string.format('unsupported_page_type=0x%x_protect=0x%x', info.type, info.protection)
        end
        local available = info.size - (address_number(cursor) - info.base)
        if available <= 0 then return false, 'invalid_region_span' end
        local amount = math.min(available, remaining)
        cursor = cursor + amount
        remaining = remaining - amount
    end
    return true
end

local function write_u32(address, value)
    local allowed, why = patchable_private_data(address, 4)
    if not allowed then return false, 'target_' .. tostring(why) end

    local before_page = page_info(address)
    if not before_page then return false, 'target_page_unavailable' end
    if before_page.state ~= 0x1000 or before_page.type ~= 0x20000 then
        return false, string.format('target_not_private_committed_type_0x%x_state_0x%x',
            before_page.type, before_page.state)
    end

    local changed_protection = false
    local original_protection = before_page.protection

    if original_protection == 0x02 then
        local old_protection = ffi.new('uint32_t[1]')
        if kernel.VirtualProtect(address, 4, 0x04, old_protection) == 0 then
            return false, string.format('VirtualProtect_to_RW_failed_error_%d',
                tonumber(kernel.GetLastError()))
        end
        changed_protection = true
        if tonumber(old_protection[0]) ~= original_protection then
            -- Restore immediately if Windows reports an unexpected original protection.
            local ignored = ffi.new('uint32_t[1]')
            kernel.VirtualProtect(address, 4, tonumber(old_protection[0]), ignored)
            return false, string.format(
                'VirtualProtect_unexpected_old_protection_expected_0x%x_got_0x%x',
                original_protection, tonumber(old_protection[0]))
        end

        local writable_page = page_info(address)
        if not writable_page or writable_page.state ~= 0x1000
            or writable_page.type ~= 0x20000 or writable_page.protection ~= 0x04 then
            local ignored = ffi.new('uint32_t[1]')
            kernel.VirtualProtect(address, 4, original_protection, ignored)
            return false, 'VirtualProtect_RW_verification_failed'
        end
    elseif original_protection ~= 0x04 then
        return false, string.format('unsupported_original_protection_0x%x',
            original_protection)
    end

    local function restore_protection()
        if not changed_protection then return true end
        local previous = ffi.new('uint32_t[1]')
        if kernel.VirtualProtect(address, 4, original_protection, previous) == 0 then
            return false, string.format('VirtualProtect_restore_failed_error_%d',
                tonumber(kernel.GetLastError()))
        end
        local restored = page_info(address)
        if not restored or restored.state ~= before_page.state
            or restored.type ~= before_page.type
            or restored.protection ~= original_protection
            or restored.allocation ~= before_page.allocation then
            return false, string.format(
                'restored_page_mismatch_expected_type_0x%x_protect_0x%x_alloc_%.0f',
                before_page.type, original_protection, before_page.allocation)

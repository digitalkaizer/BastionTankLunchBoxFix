        end
        changed_protection = false
        return true
    end

    local data = ffi.new('uint32_t[1]', value)
    local count = ffi.new('size_t[1]')
    local result = kernel.WriteProcessMemory(process, address, data, 4, count)
    local write_error = 0
    if result == 0 or tonumber(count[0]) ~= 4 then
        write_error = tonumber(kernel.GetLastError())
    end

    -- Restore the page BEFORE doing anything else with the result.
    local restored_ok, restore_error = restore_protection()
    if not restored_ok then
        return false, 'FATAL_' .. tostring(restore_error)
    end

    if result == 0 or tonumber(count[0]) ~= 4 then
        return false, string.format('WriteProcessMemory_failed_error_%d_written_%d',
            write_error, tonumber(count[0]))
    end

    local check = read_memory(address, 4)
    if not check or u32(check) ~= value then return false, 'write_verification_failed' end

    local after_page = page_info(address)
    if not after_page then return false, 'post_write_page_unavailable' end
    if after_page.state ~= before_page.state or after_page.type ~= before_page.type
        or after_page.protection ~= original_protection
        or after_page.allocation ~= before_page.allocation then
        return false, string.format(
            'page_not_restored_before_type_0x%x_protect_0x%x_after_type_0x%x_protect_0x%x',
            before_page.type,original_protection,after_page.type,after_page.protection)
    end
    return true
end

-- Unique serialized Bastion HealthComponent prefix in the current build.
local BASTION_HEADER =
    '\x40\x1f\x00\x00\x00\x00\x00\x00' ..
    '\x00\x00\x00\x00\x00\x00\x00\x00' ..
    '\x01\x00\x00\x00\x00\x00\x00\x00' ..
    '\x70\x11\x01\x00\x00\x40\x1c\xc6'

local ZONE0 = 520
local STRIDE = 552
local ZONE_HASH = 96
local ARMOR = 216
local HEALTH = 232
local MAIN = 248

local targets = {
    -- index, hash, vanilla armor, hp, vanilla main, desired armor, desired main
    { 6,  0x91f0b029, 2, 250, 0x00000000, 4, 0x00000000 },
    { 7,  0xd7533836, 2, 100, 0x00000000, 4, 0x00000000 },
    { 8,  0x04361a85, 2, 100, 0x00000000, 4, 0x00000000 },
    { 9,  0xf72a6714, 2, 100, 0x00000000, 4, 0x00000000 },
    { 10, 0x4ad0b30a, 2, 100, 0x00000000, 4, 0x00000000 },
    { 11, 0xb01597a3, 2, 100, 0x00000000, 4, 0x00000000 },

    { 16, 0x33ed0341, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 17, 0xfc7deb01, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 18, 0xe7ae77b1, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 19, 0x80ad77d2, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 20, 0xdc211672, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 21, 0xbfb691a6, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 22, 0x441c0eb0, 4, 200, 0x3f800000, 4, 0x00000000 },
    { 23, 0x6806d9c0, 4, 200, 0x3f800000, 4, 0x00000000 },
}

local function zone_address(candidate, index)
    return candidate + ZONE0 + index * STRIDE
end

local function field_u32(address)
    local b = read_memory(address, 4)
    return b and u32(b) or nil
end

local function validate(candidate)
    local h = read_memory(candidate, #BASTION_HEADER)
    if h ~= BASTION_HEADER then return false, 'bastion_header_mismatch' end

    for _,t in ipairs(targets) do
        local index, hash, vanilla_armor, hp, vanilla_main, desired_armor, desired_main =
            t[1],t[2],t[3],t[4],t[5],t[6],t[7]
        local zone = zone_address(candidate, index)
        local got_hash  = field_u32(zone + ZONE_HASH)
        local got_armor = field_u32(zone + ARMOR)
        local got_hp    = field_u32(zone + HEALTH)
        local got_main  = field_u32(zone + MAIN)
        if not got_hash or not got_armor or not got_hp or not got_main then
            return false, 'zone_unreadable_' .. tostring(index)
        end
        if got_hash ~= hash then return false, 'zone_hash_mismatch_' .. tostring(index) end
        if got_hp ~= hp then return false, 'health_mismatch_' .. tostring(index) end
        if got_armor ~= vanilla_armor and got_armor ~= desired_armor then
            return false, 'armor_mismatch_' .. tostring(index) .. '_got_' .. tostring(got_armor)
        end
        if got_main ~= vanilla_main and got_main ~= desired_main then
            return false, string.format('main_transfer_mismatch_%d_got_0x%08x', index, got_main)
        end
    end
    return true
end

local function plan(candidate)
    local actions = {}
    for _,t in ipairs(targets) do
        local index, desired_armor, desired_main = t[1], t[6], t[7]
        local zone = zone_address(candidate, index)
        local armor = field_u32(zone + ARMOR)
        local main  = field_u32(zone + MAIN)
        if not armor or not main then return nil, 'target_unreadable_' .. tostring(index) end

        -- ONLY CHANGE FROM THE WORKING v13 PATCH PLAN:
        -- gate the already-proven field writes behind the selected configuration.
        if index <= 11 and OPT_HEAVY_ARMOR and armor ~= desired_armor then
            actions[#actions+1] = {
                address=zone+ARMOR,before=armor,after=desired_armor,label='bin_armor_'..index
            }
        end
        if index <= 11 and OPT_LUNCH_TRANSFER and main ~= 0x00000000 then
            actions[#actions+1] = {
                address=zone+MAIN,before=main,after=0x00000000,label='bin_main_'..index
            }
        end
        if index >= 16 and OPT_SKIRTS_TRANSFER and main ~= desired_main then
            actions[#actions+1] = {
                address=zone+MAIN,before=main,after=desired_main,label='skirt_main_'..index
            }
        end
    end
    for _,a in ipairs(actions) do
        local ok, why = patchable_private_data(a.address, 4)
        if not ok then return nil, a.label .. '_' .. tostring(why) end
    end
    return actions
end

local function apply(candidate)
    local valid, reason = validate(candidate)
    if not valid then return false, reason, 0 end
    local actions, why = plan(candidate)
    if not actions then return false, why, 0 end
    if #actions == 0 then return true, 'already_applied', 0 end

    local completed = {}
    local current_rollback_ok = true
    for _,a in ipairs(actions) do
        local current = field_u32(a.address)
        if current ~= a.before then why = a.label .. '_changed_before_write'; break end
        local ok, err = write_u32(a.address, a.after)
        if not ok then
            why = a.label .. '_' .. tostring(err)
            local observed = field_u32(a.address)
            if observed == a.after then
                local restored = write_u32(a.address, a.before)
                if not restored then current_rollback_ok = false end
            elseif observed ~= a.before then
                current_rollback_ok = false
                why = why .. '_unexpected_value_after_failure_' .. tostring(observed)
            end
            break
        end
        completed[#completed+1] = a
    end

    if #completed ~= #actions then
        local rollback_ok = current_rollback_ok
        for i=#completed,1,-1 do
            local a = completed[i]
            local restored = write_u32(a.address, a.before)
            if not restored then rollback_ok = false end
        end
        return false, tostring(why) .. (rollback_ok and '; rolled_back' or '; ROLLBACK_FAILED'), #completed
    end


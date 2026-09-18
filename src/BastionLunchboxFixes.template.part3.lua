    local after_ok, after_reason = validate(candidate)
    if not after_ok then return false, 'post_write_' .. tostring(after_reason), #completed end
    local remaining, plan_reason = plan(candidate)
    if not remaining then return false, 'post_write_' .. tostring(plan_reason), #completed end
    if #remaining ~= 0 then return false, 'post_write_plan_not_empty_' .. tostring(#remaining), #completed end
    return true, 'applied', #completed
end

local TARGET_REGION_SIZE = 35590144
local TARGET_OFFSET = 0x994006
local MAX_ADDR = 0x7fffffffffff
local START_TICK = 600
local RETRY_INTERVAL = 300
local MAX_ATTEMPTS = 16

local locator = {
    attempts=0, regions=0, readonly_private=0, exact_size=0, offset_candidates=0,
    valid=0, first_reason=nil, last_reason=nil, last_region_base=nil,
    last_region_size=nil, last_candidate=nil
}

local function protection_base(value)
    if math.floor(value / 0x100) % 2 == 1 then return -1 end -- PAGE_GUARD
    return value % 0x100
end

local function describe_page(address)
    local r = ffi.new('KzrBastionMemoryRegionV8[1]')
    if query_region(address, r, ffi.sizeof(r[0])) == 0 then return 'VirtualQuery_failed' end
    return string.format('base=%.0f alloc=%.0f type=0x%x protect=0x%x size=%d',
        address_number(r[0].base),address_number(r[0].allocation_base),
        tonumber(r[0].type),tonumber(r[0].protection),tonumber(r[0].size))
end

local function inspect_region(base_num, size)
    if size <= TARGET_OFFSET + #BASTION_HEADER then return nil end
    locator.offset_candidates = locator.offset_candidates + 1
    locator.last_region_base = base_num
    locator.last_region_size = size
    local candidate = ffi.cast('uint8_t *', base_num + TARGET_OFFSET)
    locator.last_candidate = address_number(candidate)
    local ok, reason = validate(candidate)
    if not ok then
        locator.first_reason = locator.first_reason or reason
        locator.last_reason = reason
        return nil
    end
    locator.valid = locator.valid + 1
    return candidate
end

local function locate_bastion()
    locator.attempts = locator.attempts + 1
    local cursor = 0x10000
    local region = ffi.new('KzrBastionMemoryRegionV8[1]')
    local fallback = {}
    local regions_this_attempt = 0
    local ro_this_attempt = 0
    local exact_this_attempt = 0

    while cursor < MAX_ADDR do
        local ptr = ffi.cast('uint8_t *', cursor)
        if query_region(ptr, region, ffi.sizeof(region[0])) == 0 then break end
        local base_num = address_number(region[0].base)
        local size = tonumber(region[0].size)
        local next_num = base_num + size
        if size <= 0 or next_num <= cursor then break end
        cursor = next_num
        regions_this_attempt = regions_this_attempt + 1

        local p = protection_base(tonumber(region[0].protection))
        if tonumber(region[0].state) == 0x1000
            and tonumber(region[0].type) == 0x20000 and p == 0x02 then
            ro_this_attempt = ro_this_attempt + 1
            if size == TARGET_REGION_SIZE then
                exact_this_attempt = exact_this_attempt + 1
                local candidate = inspect_region(base_num, size)
                if candidate then
                    locator.regions = locator.regions + regions_this_attempt
                    locator.readonly_private = locator.readonly_private + ro_this_attempt
                    locator.exact_size = locator.exact_size + exact_this_attempt
                    return candidate, 'exact_size'
                end
            elseif size > TARGET_OFFSET + 14000 and size >= 16 * 1024 * 1024 then
                fallback[#fallback+1] = {base=base_num,size=size}
            end
        end
    end

    -- Size is a strong discriminator, but do not make it a single point of failure.
    -- If the build maps the same DataLibrary into a slightly different large RO
    -- region, test the same proven serialized offset there too.
    for _,r in ipairs(fallback) do
        local candidate = inspect_region(r.base, r.size)
        if candidate then
            locator.regions = locator.regions + regions_this_attempt
            locator.readonly_private = locator.readonly_private + ro_this_attempt
            locator.exact_size = locator.exact_size + exact_this_attempt
            return candidate, 'large_ro_fallback'
        end
    end

    locator.regions = locator.regions + regions_this_attempt
    locator.readonly_private = locator.readonly_private + ro_this_attempt
    locator.exact_size = locator.exact_size + exact_this_attempt
    return nil, 'not_ready'
end


local original_update=update
local callback
local ticks=0
local next_attempt=START_TICK

local function stop_callback()
end

local function finish_success(candidate, mode, why, writes)
    state.done=true; state.active=true
    state.copies=1; state.writes=writes
    report(string.format(
        'APPLIED: candidate=%.0f mode=%s result=%s writes=%d attempts=%d; protected_data_writer=VirtualProtect_RW_then_restore; configuration=' .. CONFIG_LABEL .. '; HP/durability unchanged; page=%s',
        address_number(candidate),tostring(mode),tostring(why),writes,locator.attempts,describe_page(candidate)))
    stop_callback()
end

local function finish_failure(reason)
    state.done=true; state.active=false
    report(string.format(
        'STOPPED: %s; attempts=%d regions=%d readonly_private=%d exact_size=%d offset_candidates=%d valid=%d first_reason=%s last_reason=%s last_region_base=%s last_region_size=%s last_candidate=%s',
        tostring(reason),locator.attempts,locator.regions,locator.readonly_private,
        locator.exact_size,locator.offset_candidates,locator.valid,
        tostring(locator.first_reason),tostring(locator.last_reason),
        tostring(locator.last_region_base),tostring(locator.last_region_size),tostring(locator.last_candidate)))
    stop_callback()
end

local function try_patch()
    if state.done then return end
    ticks=ticks+1
    if ticks < next_attempt then return end
    next_attempt = ticks + RETRY_INTERVAL

    local called,candidate,mode = pcall(locate_bastion)
    if not called then finish_failure('locator_ERROR_'..tostring(candidate)); return end

    if candidate then
        local ok, why, writes = apply(candidate)
        if ok then finish_success(candidate,mode,why,writes); return end
        finish_failure(string.format('validated Bastion structure at %.0f but apply failed: %s; target_page=%s',
            address_number(candidate),tostring(why),describe_page(zone_address(candidate,6)+ARMOR)))
        return
    end

    if locator.attempts >= MAX_ATTEMPTS then
        finish_failure('DataLibrary region never became valid at base+0x994006')
        return
    end

    report(string.format(
        'waiting for populated DataLibrary; attempt=%d/%d regions=%d readonly_private=%d exact_size=%d offset_candidates=%d first_reason=%s last_reason=%s',
        locator.attempts,MAX_ATTEMPTS,locator.regions,locator.readonly_private,
        locator.exact_size,locator.offset_candidates,tostring(locator.first_reason),tostring(locator.last_reason)))
end

local function after(...)
    try_patch()
    return ...
end
callback=function(dt,...)
    if original_update then return after(original_update(dt,...)) end
    try_patch()
end
update=callback
report('installed; exact v13 Bastion locator/writer armed; configuration=' .. CONFIG_LABEL)
return state

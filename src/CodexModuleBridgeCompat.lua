-- DigitalKaizer Bastion Lunchbox Fix v1.0.6 - Codex Module Bridge v1 compatibility
--
-- mods/codex/gun_calibration is also used by Codex Module Bridge v1.
-- When this mod wins that shared resource, preserve Bridge v1's functional
-- dispatcher behavior without claiming Bridge's global state or log identity.
--
-- Codex Module Bridge remains optional and independently distributed. If a real
-- CodexModuleBridge global is already active, this shim does not duplicate its
-- dispatcher work. Otherwise it conditionally starts the two known Bridge v1
-- gameplay modules if they are installed.
do
    if not rawget(_G, 'DigitalKaizerBastionCodexCompat') then
        local compat = {
            revision = 'digitalkaizer-bastion-compat-v1.0.6',
            modules = {},
            status = 'starting'
        }
        rawset(_G, 'DigitalKaizerBastionCodexCompat', compat)

        local function compat_report(name, status)
            compat.modules[name] = status
            print('[DigitalKaizerBastionCodexCompat] ' .. name .. ': ' .. status)
            pcall(function()
                local logger = rawget(_G, 'CowboyBingusModLoader')
                local file = logger and logger.open_log and logger.open_log('DigitalKaizerBastionLunchboxFixCompat.log')
                if not file then return end
                file:write('DigitalKaizer Bastion Lunchbox Fix - Codex Bridge v1 compatibility\n')
                file:write('revision=' .. compat.revision .. '\n')
                for module, result in pairs(compat.modules) do
                    file:write(module .. ': ' .. tostring(result) .. '\n')
                end
                file:close()
            end)
        end

        if rawget(_G, 'CodexModuleBridge') then
            compat.status = 'external_bridge_active'
            compat_report('bridge', 'external Codex Module Bridge already active; dispatcher skipped')
        else
            local application = stingray and stingray.Application
            for _, name in ipairs({
                'mods/codex/p11_self_heal',
                'mods/codex/constitution_bolt_amr',
            }) do
                local ok, available = pcall(function()
                    assert(application and type(application.can_get) == 'function',
                        'lua resource lookup unavailable')
                    return application.can_get('lua', name)
                end)

                if not ok then
                    compat_report(name, 'lookup failed: ' .. tostring(available))
                elseif not available then
                    compat_report(name, 'not installed')
                else
                    local loaded, reason = pcall(require, name)
                    compat_report(name, loaded and 'loaded' or 'load failed: ' .. tostring(reason))
                end
            end
            compat.status = 'complete'
        end
    end
end

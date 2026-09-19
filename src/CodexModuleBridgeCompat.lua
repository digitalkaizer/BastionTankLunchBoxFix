-- Bastion Lunchbox Fixes v1.0.4 compatibility prefix
--
-- mods/codex/gun_calibration is also used by Codex Module Bridge v1.
-- When this mod wins that shared resource, preserve the bridge's functional
-- behavior by conditionally starting the two independent Codex modules that
-- Bridge v1 starts. This prefix makes no gameplay changes of its own.
--
-- The real Codex Module Bridge may remain installed independently. Only one
-- gun_calibration resource can win; this prefix intentionally uses the same
-- global guard so duplicate bridge initialization is avoided if another
-- startup path has already run it.

do
    if not rawget(_G, 'CodexModuleBridge') then
        local bridge = {
            revision = 'bastion-compat-v1.0.4',
            modules = {},
            status = 'starting'
        }
        rawset(_G, 'CodexModuleBridge', bridge)

        local function bridge_report(name, status)
            bridge.modules[name] = status
            print('[CodexModuleBridge] ' .. name .. ': ' .. status)
            pcall(function()
                local logger = rawget(_G, 'CowboyBingusModLoader')
                local file = logger and logger.open_log and logger.open_log('CodexModuleBridge.log')
                if not file then return end
                file:write('Codex Module Bridge v1 compatibility via Bastion Lunchbox Fix v1.0.4\n')
                for module, result in pairs(bridge.modules) do
                    file:write(module .. ': ' .. tostring(result) .. '\n')
                end
                file:close()
            end)
        end

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
                bridge_report(name, 'lookup failed: ' .. tostring(available))
            elseif not available then
                bridge_report(name, 'not installed')
            else
                local loaded, reason = pcall(require, name)
                bridge_report(name, loaded and 'loaded' or 'load failed: ' .. tostring(reason))
            end
        end

        bridge.status = 'complete'
    end
end

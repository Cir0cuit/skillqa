# Controls: how to apply each recommendation

Settings files, highest precedence first: managed settings, `--settings`,
`.claude/settings.local.json` (this project, only you), `.claude/settings.json`
(this project, shared), `~/.claude/settings.json` (all projects). For
`enabledPlugins`, the highest file that names the plugin wins, so a project
`true` beats a user `false`. Check the effective state with
`claude plugin list --json` (`enabled`, `projectEnabled`) or the `/plugin`
Installed tab; `/status` only lists which settings files were loaded.

Plugin enable, disable and install changes reach a running session after
`/reload-plugins` (`/reload-plugins --force` when the change adds or removes
MCP tools) or in a new session. Settings changed while a session runs do not
reach its plugins until then.

## Plugins

| Goal | How |
|---|---|
| Install for this project, for you only | `claude plugin install <id> --scope local` |
| Install for everyone on the project | `claude plugin install <id> --scope project` (writes `.claude/settings.json`) |
| Install for all your projects | `claude plugin install <id> --scope user` |
| Remove a plugin | `claude plugin uninstall <id> --scope user` (or `project`, `local`) |
| Remove a marketplace and everything from it | `claude plugin marketplace remove <marketplace>` |
| Turn off everywhere, keep installed | `claude plugin disable <id> --scope user` |
| Turn off in one project, for you only | `"<id>": false` under `enabledPlugins` in that project's `.claude/settings.local.json` |
| Use only in one project | Off at user scope; `"<id>": true` in that project's `.claude/settings.local.json` |
| On demand only | Keep it disabled; when wanted, `claude plugin enable <id> --scope user` and `/reload-plugins`, then `claude plugin disable <id> --scope user`. Always pass `--scope`: without it, enable and disable write to the first settings file that names the plugin, checking local first, so run inside a project that turned the plugin off it would turn it back on there. A plugin's own off mode (ponytail: `PONYTAIL_DEFAULT_MODE=off`) can reduce what it injects, but its skills stay loadable by Claude while it is enabled |
| Turn off one plugin's hooks only | Not available. Disable the plugin, or use its own settings |
| Block one skill of an enabled plugin | `permissions.deny`: `"Skill(<plugin>:<skill>)"` and `"Skill(<plugin>:<skill> *)"` (the second also catches calls with arguments). `skillOverrides` does not affect plugin skills |
| See what a plugin costs | `claude plugin details <id>` (installed plugins only; hook-injected text is not counted) |

## Standalone skills (`~/.claude/skills`, `.claude/skills`)

| Goal | How |
|---|---|
| Delete | Remove its folder (for a symlinked skill, remove the link, and the target only if nothing else uses it) |
| Only when the user types `/name` | `skillOverrides: {"<name>": "user-invocable-only"}`, or `disable-model-invocation: true` in its SKILL.md |
| Cheaper listing | `skillOverrides: {"<name>": "name-only"}` |
| Hide completely | `skillOverrides: {"<name>": "off"}` |
| Block outright | `permissions.deny`: `"Skill(<name>)"` and `"Skill(<name> *)"` |
| Per project | Put `skillOverrides` in that project's `.claude/settings.local.json` (or `/skills`, Space, Esc) |
| Bundled Claude Code skills | `disableBundledSkills: true` turns all of them off; prefer leaving them |

## claude.ai-synced skills, plugins and connectors

| Goal | How |
|---|---|
| One synced skill off | `skillOverrides: {"anthropic-skills:<name>": "off"}` (use the full name; check the result in `/skills`), or deny rules `"Skill(anthropic-skills:<name>)"` and `"Skill(anthropic-skills:<name> *)"` |
| One synced plugin off | `claude plugin disable <name>@synced` |
| All synced plugins off | `"syncClaudeAiPlugins": false`. In `.claude/settings.local.json` it only stops loading them in that project. In `~/.claude/settings.json` it also moves them to `~/.claude/plugins/.trash/` (deleted after 30 days), so turning one back on later downloads it again. Not read from `.claude/settings.json` |
| All synced skills off | `"syncClaudeAiSkills": false`, with the same files and the same `.trash` behaviour (`~/.claude/skills/.trash/`) |
| Connectors off | `"disableClaudeAiConnectors": true` in any settings file; one connector: `deniedMcpServers: [{"serverName": "claude.ai <Name>"}]` or `/mcp` per project |
| Remove at the source | claude.ai settings for skills and plugins; claude.ai/customize/connectors for connectors |

## MCP servers

| Goal | How |
|---|---|
| Remove | `claude mcp remove <name> --scope user` (or `local`, `project`) |
| Off in one project, keep the config | `/mcp`, select it, disable (stored in `~/.claude.json` as `disabledMcpServers` for that project) |
| Block by name | `deniedMcpServers: [{"serverName": "<name>"}]` in a settings file. For a plugin's own MCP servers, disable the plugin instead: a deny entry is reported not to stop them (knowledge-work-plugins issue #933, not confirmed) |
| Reject a project's `.mcp.json` server | `disabledMcpjsonServers: ["<name>"]` |
| Keep its tools out of context | Deferred loading is the default; `"alwaysLoad": false` in its config forces it |

# Native counterparts

What Claude Code already does, so an extension that only repeats it is not
needed. Checked against the Claude Code docs in November 2026; features
change, so confirm a row against code.claude.com/docs before relying on it in
a verdict.

| An extension offers | Native feature | How to use it |
|---|---|---|
| Multi-agent orchestration, fan-out, cross-checking agents | Workflows (Workflow tool, ultracode mode, `/workflows`) | Say "use a workflow to ..." or start with `ultracode:`; `/effort ultracode` for a whole session; `/deep-research <question>` |
| Parallel units of the same change | `/batch` | `/batch <instruction>` (needs a git repo) |
| Delegated workers with their own context (reviewer, researcher, refactorer) | Subagents: built-in Explore, Plan, general-purpose; custom agents in `~/.claude/agents/` or `.claude/agents/` | Ask for the agent by name, `@agent`, or `claude --agent <name>` |
| A team of sessions with shared tasks | Agent teams (experimental) | `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
| Plan before editing, wait for approval | Plan mode | Shift+Tab, `/plan`, `--permission-mode plan` |
| Brainstorm, spec and plan pipeline with approval gates | Plan mode plus a workflow for the execution | `/plan`, then "use a workflow to implement the plan" |
| Code review of a diff, branch or PR | `/code-review` (alias `/review`), effort levels, `--fix`, `--comment` | `/code-review high <target>` |
| Independent multi-agent bug review in the cloud | `/code-review ultra` | `/code-review ultra [PR]` (billed after free runs) |
| Security review of a diff | `/security-review` | `/security-review` |
| Cleanup and simplification review | `/simplify` | `/simplify [target]` |
| Persistent instructions and learned notes | CLAUDE.md files, `.claude/rules/`, auto memory | `/memory`, `/init` |
| Project setup checks | `/init`, `/doctor` | `/init`, `/doctor` |
| Isolated parallel checkouts | Git worktrees | `claude --worktree <name>`, subagent `isolation: worktree` |
| Browser automation | Claude in Chrome | `claude --chrome`, `/chrome` |
| Web search and page fetching, cross-checked research | WebSearch, WebFetch, `/deep-research` | Ask; `/deep-research <question>` |
| Reminders, polling, recurring prompts | `/loop`, cron tools, `/schedule` (cloud) | `/loop 5m <prompt>`, `/schedule` |
| Background sessions and monitoring | `claude --bg`, `claude agents`, `/tasks`, Monitor tool | `claude --bg <prompt>` |
| Format, block or notify on events | Hooks in settings | `/update-config`, or a `hooks` block |
| Status bar | Status line | `/statusline` |
| Response style for a session (concise, explanatory, learning) | Output styles | `/output-style <name>` |
| Undo edits, roll back, summarize part of a session | Checkpoints | `/rewind` or Esc Esc |
| Go to definition, references, type errors | LSP plugins from the official marketplace | `/plugin install <server>-lsp@claude-plugins-official` (named after the language server, for example `clangd-lsp` for C/C++; list at code.claude.com/docs/en/plugins/code-intelligence) |
| Fewer permission prompts | Permission modes, `/permissions`, `/fewer-permission-prompts` | Shift+Tab, `/fewer-permission-prompts` |
| Context and cost management | `/context`, `/compact`, `/clear`, `/usage` | as named |
| Checking a plugin before trusting it | `claude plugin details` (token cost), `claude plugin validate`, `claude plugin eval` | as named |
| Finding unused or costly skills and plugins | `/skill-doctor` (where available), `/doctor`, "Not used recently" in the `/plugin` Installed tab, `/usage` | as named |
| Verify a change in the running app | Bundled `/run` and `/verify` skills | `/run`, `/verify` |

Bundled skills and their names also change between versions: list the current
ones in the session's skill list or `/skills` before claiming one exists.

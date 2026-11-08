# skillqa: Skill Quality Assurance for Claude Code

## Don’t keep or install token-eating garbage just because some wannabe AI vibe coding influencer told you to!

**Security scanners tell you whether an extension is dangerous. skillqa tells
you whether it is worth having.**

Claude Code grows with skills, plugins, marketplaces and MCP servers. Each one
is easy to add and easy to forget, yet many of them cost you something in every
session: descriptions that sit in the context window, hooks that inject
instructions into every prompt, MCP servers that add their own system-prompt
text. Some repeat what Claude Code already does natively. Some never worked
because their setup was never finished. Some quietly overrule your own
instructions.

skillqa keeps the extensions that earn their place, refuses the ones that
don't, and helps you act on what it finds.

## What it does

**An install gate.** Before Claude installs, enables or adds an extension,
skillqa reads it (without running any of its code), researches it and gives a
verdict. If it is garbage, Claude refuses and says why, and points to the
native feature or a better tool that does the job. You can still insist.
The gate needs one line in your `CLAUDE.md`; see [Install](#install).

**A full scan.** Run `/skillqa` and it inventories everything that extends
your Claude Code (user and project skills, plugins, skills and plugins synced
from claude.ai, marketplaces, MCP servers and claude.ai connectors) and sorts
each one into a verdict, with evidence:

| Verdict | Meaning |
|---|---|
| **Total garbage** | Does nothing useful, or a native Claude Code feature does its main job. Remove it. |
| **Questionable** | Narrow use, mixed results or high cost. Keep it, but limit it, with the exact setting. |
| **Not useful at the moment** | Fine elsewhere, no use in this project or task. Turn it off here only. |
| **Fix** | Worth keeping but broken. You get the diagnosis and the fix, never "remove". |
| **Keep** | Earns its place. |

Nothing changes until you confirm, with one exception you set up yourself: an
item you banned with "remove on sight" is removed when it is found. Every
proposed change is listed on its own, with what you lose if you apply it.

## Why you can trust a verdict

- **Evidence, not opinion.** Every verdict cites the extension's own code
  (file and line), its repository and issues, or the Claude Code
  documentation for the native feature it duplicates. An author's own claims
  and benchmarks count as weak evidence.
- **It knows why things are there.** Before rating anything, skillqa reads
  your past Claude Code sessions, memory notes and CLAUDE.md files for what
  you asked for and what was built for you. It does not second-guess a
  decision you already made.
- **What you set up on purpose is protected.** Security tooling such as
  [skill-inspector](https://github.com/NVIDIA/skillspector/tree/main/skills/skill-inspector) or [SkillSpector](https://github.com/NVIDIA/skillspector), anything you deliberately installed or had
  built (with the hooks, services and profiles around it), and your own
  skills are never offered for removal or limiting. You can add anything else
  to an allowlist.
- **Broken is not useless.** A tool that fails but does something nothing
  else does gets fixed, not thrown out.
- **Overlap must be proven.** "Tool X covers tool Y" only counts when, for
  every capability of Y, a matching tool of X is named. "Use the native
  feature instead" names the feature and how to invoke it, for example
  [plan mode](https://code.claude.com/docs/en/permission-modes),
  [workflows](https://code.claude.com/docs/en/workflows) or
  [memory](https://code.claude.com/docs/en/memory).
- **It measures the real cost**, including what most listings miss:
  always-on tokens ([`claude plugin details`](https://code.claude.com/docs/en/plugins/install)), hooks that add text to every
  session, prompt or subagent, MCP server instructions, hooks on every tool
  call, files written into your projects, and usage counters showing what you
  actually use.
- **It never runs the extension** to find out what it does. It reads it.

## Example

An abridged scan of a web project, with illustrative names:

```
skillqa scan: ~/projects/web-shop, 2026-11-08

Total garbage (remove now)
- planning-pack (plugin, user): a brainstorm-plan-execute pipeline whose main job
  plan mode and workflows already do; its start-up hook orders a skill check before every reply.
  Use instead: plan mode (Shift+Tab or /plan), workflows ("use a workflow to ...").
  Evidence: hooks/session-start:12; code.claude.com/docs/en/workflows.
  Remove: `claude plugin uninstall planning-pack@example-marketplace --scope user`

Questionable (limit it)
- web-data@synced: about 5,300 tokens in every session, never set up, and its skill
  tells Claude not to use WebFetch.
  Recommendation: off until you need the paid service.  Set: `claude plugin disable web-data@synced --scope user`.

Not useful at the moment (~/projects/web-shop)
- binary-analysis (MCP server): nothing to reverse-engineer here, about 2,400 tokens per session.
  Set: `deniedMcpServers` entry in this project's .claude/settings.local.json.

Fix (keep it; it is broken or not working as intended)
- crawler (MCP server): your self-hosted replacement for a paid scraping API, and the only
  tool here that crawls whole sites. Its container is down when sessions start, so no tools load.
  Fix: run the container as an always-on service (for example a podman quadlet).

Keep
- search (MCP server), skill-inspector, frontend-design
```

Before an install, the answer looks like this:

```
example-memory@example-marketplace: Total garbage.
What it adds: 1 skill, a SessionStart hook that injects 3 KB of rules.
Why: Claude Code's CLAUDE.md files and auto memory do its main job; its notes go into
a project file that git shares.
Use instead: /memory (CLAUDE.md, CLAUDE.local.md for personal notes, auto memory).
Offer: nothing. Say so if you want it anyway.
Evidence: skills/memory/SKILL.md:4,75; code.claude.com/docs/en/memory
```

## Install

You need Claude Code, Python 3 and git. There is nothing else to install:
the scripts use only the Python standard library.

Clone the repository and link the skill into your personal skills folder.

**Linux and macOS:**

```bash
git clone https://github.com/Cir0cuit/skillqa.git ~/skillqa
mkdir -p ~/.claude/skills && ln -s ~/skillqa/skillqa ~/.claude/skills/skillqa
```

<details>
<summary><b>Windows (PowerShell)</b></summary>

```powershell
git clone https://github.com/Cir0cuit/skillqa.git "$HOME\skillqa"
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
New-Item -ItemType Junction -Path "$HOME\.claude\skills\skillqa" -Target "$HOME\skillqa\skillqa"
```

A directory junction needs no administrator rights or Developer Mode, unlike a
symbolic link. Check that `/skills` in Claude Code lists skillqa; if it does
not, copy the folder instead, and copy it again after each update:
`Copy-Item -Recurse "$HOME\skillqa\skillqa" "$HOME\.claude\skills\skillqa"`.

Python on Windows is usually started as `py -3` or `python`; skillqa tells
Claude to use those there. Update with `git -C "$HOME\skillqa" pull`. Your
personal `CLAUDE.md` is `%USERPROFILE%\.claude\CLAUDE.md`.

</details>

To update on Linux and macOS, run `git -C ~/skillqa pull`.

Then add this to your personal `CLAUDE.md` (`~/.claude/CLAUDE.md`):

```
Before installing, enabling or adding any skill, plugin, marketplace or MCP
server, run the skillqa skill on it and follow its verdict.
```

The line is required for the install gate. When many skills are installed,
Claude Code shortens their descriptions in its listing, so a skill's
description alone cannot be relied on to trigger before an install.

skillqa was developed and tested with Claude Code 2.1.319 on Linux. The
scripts are written to run on Windows too (paths, the `claude.exe` and npm
`claude.cmd` launchers, console encoding, Windows-format transcripts), and
their history search was checked against real Windows transcripts, but the
skill has not yet been run end to end on Windows or macOS.

## Use

- `/skillqa` scans everything installed. Inside a git repository the scan
  also judges what fits that project; elsewhere it judges globally.
- `/skillqa <plugin id, marketplace, repository URL or folder>` vets one
  extension.
- Or ask Claude to install something: with the CLAUDE.md line in place,
  skillqa runs first.

A full scan researches every rated item, in parallel when you allow Claude
Code workflows, so it takes a while and is not cheap: one scan of a setup
with about 30 skills and plugins, 7 MCP servers and 55 claude.ai connectors
used about 1.2 million tokens across its research agents. An install check
covers one item and is quick.

## Your decisions

skillqa keeps your standing decisions in `~/.claude/skillqa/known-verdicts.md`,
outside this repository, and applies them before any research of its own:

- **Allowlist**: items it must never offer for removal or limiting.
- **Bans**: items it must refuse outright, and optionally remove on sight.
- **Accepted or overridden verdicts**, so the next scan does not ask again.

It creates and extends the file as you decide;
`skillqa/references/known-verdicts.template.md` shows the format.

## Privacy

Both scripts only read local files. `history.py` reads your Claude Code
transcripts and memory notes; of tool output it reads only your answers to
Claude's questions and your reasons for rejecting a tool call, and it masks
anything shaped like a key, token or password before printing. `inventory.py` never prints
environment values, headers or command-line flag values from MCP server
definitions. Research uses the web search Claude Code already has, with the
names of the extensions being checked.

## What it does not do

- It does not judge security. Pair it with a security scanner such as
  [skill-inspector](https://github.com/NVIDIA/skillspector/tree/main/skills/skill-inspector);
  skillqa points to it for anything from an untrusted source.
- It cannot see what happened on claude.ai, on other machines, or in
  transcripts that Claude Code has already deleted. When the history is
  silent about an item that might have been set up on purpose, it asks you.
- It does not change anything on its own, apart from an item you banned with
  "remove on sight".

## What is inside

```
skillqa/SKILL.md                              verdicts, install gate, scan, report format, rules
skillqa/scripts/inventory.py                  read-only inventory of everything installed
skillqa/scripts/history.py                    what you and past sessions said about each item
skillqa/references/categories.md              exact verdict definitions and tie-breakers
skillqa/references/research.md                how each verdict is researched and evidenced
skillqa/references/native-counterparts.md     built-in features an extension may duplicate
skillqa/references/controls.md                the commands and settings behind each recommendation
skillqa/references/known-verdicts.template.md format of your decisions file
```

Both scripts check their own secret filters. From the repository's top
folder:

```bash
python3 skillqa/scripts/inventory.py --self-test
python3 skillqa/scripts/history.py --self-test
```

On Windows, use `py -3` in place of `python3`.

## License

MIT. See [LICENSE](LICENSE).

# Research protocol

Every rated item needs evidence about the item itself, beyond its own
description. Use WebSearch and WebFetch (or a search MCP server the user has,
such as searxng), plus the files on disk.

## Questions to answer

0. **Why is it here?** Use the history output the main agent passed to you;
   if you must run it yourself, run
   `python3 "$HOME/.claude/skills/skillqa/scripts/history.py" <bare name> <id> --current-session <session id>`
   (`py -3` on Windows) and read the memory notes it points to. No hits proves nothing
   (old transcripts are deleted, other machines are missing): then look for
   other signs of deliberate setup and ask the user while in doubt. Who installed it, when, and what did the user say?
   If the user asked for it, or a session built it at their request, it is
   protected (SKILL.md, "Protected items"): your job is then to check it
   works and fix it, not to judge whether it should stay. Quote the user's
   words in the evidence.
1. **What does it actually do?** From its code, SKILL.md files, hooks, MCP
   tool list and MCP server `instructions`, not from its README's promises.
2. **Which native feature or installed tool covers it, fully or partly?**
   Prove it: list what the item does, and for each capability name the tool
   or feature that also does it. One uncovered capability (for example a
   whole-site crawl that the other scraper has no tool for) means it is not
   covered. Check
   [native-counterparts.md](native-counterparts.md), then confirm against the
   current Claude Code docs (code.claude.com/docs), because features change.
3. **What does it cost while installed?**
   - Installed plugins: `claude plugin details <id>` gives the always-on
     tokens. Before an install that command fails; count from the files
     instead: skill, agent and command descriptions, MCP servers, and hooks.
   - Hooks on SessionStart, UserPromptSubmit, UserPromptExpansion,
     PostModelSwitch or SubagentStart, and hook files that return
     `additionalContext`, put text into the model's context; read them.
   - MCP server `instructions` enter the system prompt of every session where
     the server is on.
   - Hooks on every tool call, tools that load up front (`alwaysLoad`), files
     it writes into projects or the home folder, telemetry and network calls.
4. **Does it fight the user?** Start-up instructions that compete with the
   user's CLAUDE.md; "you MUST", "always use this", "no exceptions" or
   "instead of WebFetch" directives in skills, hooks or server instructions;
   conflicts with other installed extensions or with ultracode.
5. **Does it work, and for whom?** Independent results: issues and their
   answers, discussions, reviews, benchmarks by people other than the author.
   Last release and commit dates. Whether it needs another product, a paid
   account or credentials that were never set up. Which project types it is
   for.
   An MCP server reached over the network (SSE or HTTP) whose backend is not
   running when a session starts is marked failed and lists no tools, so a
   hook that starts the backend on first use can never fire; check how the
   backend is started.
6. **Has the user used it?** The usage counters in the inventory
   (`usage.pluginUsage`, `usage.skillUsage`, with `numStartups` for scale),
   the `/skill-doctor` report if available, and "Not used recently" in the
   `/plugin` Installed tab.

## Where to look, strongest first

- For intent: past conversations and memory notes (history.py). Nothing
  outranks what the user said about the item.
- For what it does: the extension's own code (path:line).
- Independent evidence: GitHub issues and discussions, Hacker News, Reddit,
  blog posts, benchmarks by third parties.
- The official Claude Code docs for the overlapping native feature.
- The repository's README, changelog and the author's benchmark (weak: the
  author's claims).
- Stars and download counts (weakest: popularity is not usefulness).

## Evidence bar

Every verdict cites at least one source about the item itself (its code at
path:line, its repository or issues, its marketplace page), or says "no
public footprint" and lists the searches tried. In addition:

- **Total garbage**: the docs URL of the native feature that does its main
  job, or code reading that shows it does nothing useful (path:line), plus
  evidence that nobody deliberately set it up: no history, no other signs of
  deliberate setup, and, if any doubt remains, the user's answer.
- **Fix**: the evidence of the fault (logs, start-up errors, config, code)
  and the fix, tested where that can be done without running the extension.
- **Questionable**: evidence of narrow scope, mixed results or high cost,
  plus the exact limiting setting.
- **Not useful at the moment**: the project facts (stack, task) that make it
  irrelevant here.

## Practical limits

- Group similar items into one research task (for example all unused
  claude.ai connectors, or all document-format skills).
- Time-box each item; when evidence stays thin, choose the milder verdict and
  say what is missing.
- Record every source as a URL or path:line next to the verdict.
- Never run the extension's scripts, installers, hooks or MCP servers to test
  them.

---
name: skillqa
description: Quality and usefulness review of Claude Code skills, plugins, marketplaces and MCP servers (not security; skill-inspector covers that). Use BEFORE installing, enabling or adding any skill, plugin, marketplace or MCP server, to refuse garbage and name the native feature or better tool instead. Use when the user runs /skillqa, or asks which installed skills, plugins or MCP servers are useless, redundant, in the way, or wrong for the current project.
argument-hint: "[name, id, URL or path to evaluate; nothing for a full scan]"
---

# skillqa

Keep only extensions that contribute to the user's work. Judge usefulness and
quality: what an extension does, whether Claude Code already does it natively,
what it costs in every session, and whether it fits this user and this
project. Security is out of scope; for an untrusted source (anything outside
`claude-plugins-official`, or marked community-managed there), suggest the
skill-inspector skill as well. If skill-inspector is turned off in this
project, report it as Fix and offer to turn it back on here; ask first, since
the user may have turned it off.

**Which mode.** If an argument names a target, or the conversation has a
pending install, enable or add (asked for by the user or about to be done by
Claude), evaluate that target: Mode A. Scan only when there is no such target,
for a bare `/skillqa` or a request to review what is installed: Mode B.

**Standing decisions.** Before rating anything, read from disk, even if a copy
is already in context: `~/.claude/CLAUDE.md`, the project's `CLAUDE.md`,
`.claude/CLAUDE.md` and `CLAUDE.local.md`, and the user's decisions file
`~/.claude/skillqa/known-verdicts.md` (format:
[references/known-verdicts.template.md](references/known-verdicts.template.md);
if it is missing, there are none yet). A plugin set to false, a skill set to
"off" or a denied MCP server in a project's settings is also an earlier
decision: mention it, and ask before reversing it.

**History comes first.** Before rating any item, find out why it is there:

```bash
python3 "$HOME/.claude/skills/skillqa/scripts/history.py" <name> [<name> ...] --current-session ${CLAUDE_SESSION_ID}
```

On Windows, call Python as `py -3` (or `python`) instead of `python3`; the
`"$HOME/..."` path works in both PowerShell and Git Bash.

It searches every past session in every project, the memory notes, the
CLAUDE.md files, the decisions file and the hook scripts. USER lines are what
the user typed (newest first, including this session's corrections), their
answers to Claude's questions ("answered: …", with the question after it) and
the reasons they gave when rejecting a tool call; PROMPT
lines are `claude -p` prompts Claude may have written itself; SETUP lines are
commands run and files written for the item. Pass both the bare name and the
id (`ponytail ponytail@ponytail`): the id finds setup commands, the bare name
finds what the user said. Read the memory notes
it points to in full. A verdict that ignores this evidence is invalid.

No hits proves nothing: transcripts are deleted after `cleanupPeriodDays`, and
sessions on other machines are missing. For an item with no history, look for
other signs of deliberate setup (custom configuration, wrapper scripts, hooks
or services around it, a non-default install source); while any doubt
remains, ask the user before rating it below Keep.

## Protected items (allowlist)

Never recommend removing, uninstalling, disabling, denying or limiting:

1. **Security tooling for extensions**: skill-inspector, SkillSpector and
   anything like them, in every form (skill, CLI, MCP server, hook). skillqa
   hands security to them; judging them is outside its scope.
2. **Anything the user deliberately set up**: history shows the user asked
   for it, or a session built it at their request (install commands, a memory
   note, a CLAUDE.md section). This covers everything built around it too:
   hooks, services, containers, profiles, companion skills.
3. **The user's own skills and uploads.**
4. **Every entry in the allowlist** of the decisions file.

A protected item is rated **Keep**, or **Fix** when it is broken or does not
work as intended. A cost or overlap worth knowing goes in the report's notes
only; no setting change is offered for it unless the user names that item.
A broad request ("turn off what is irrelevant here", "clean up", "remove what
is unused") never covers a protected item: carry it out for the unprotected
items, list the protected ones it would have touched, and ask. Only the user
can decide to limit or remove a protected item, and skillqa never suggests
it.

**Ban versus protection.** A ban the user wrote outranks protection only when
it names the item itself. If an item is both protected and swept in by a
broad ban (a publisher, a marketplace), change nothing: quote both entries and
ask the user.

## Verdicts

Use exactly these, as defined in [references/categories.md](references/categories.md):

- **Total garbage**: remove it now and do not use it. Only for an extension
  that does nothing useful, or whose main job a native Claude Code feature
  already does (name that feature and how to invoke it). Example: superpowers;
  use workflows (ultracode) instead.
- **Questionable**: narrow use, mixed results. Give an exact usage
  recommendation and the setting that enforces it. Example: ponytail; keep it
  disabled and switch it on only when the user asks for it.
- **Not useful at the moment**: fine in general, no use in the current project
  or task. Rate this only inside a project (a git repository) or when the
  session has a task. Recommend the scope that fixes it, usually disabling it
  for this project only.
- **Fix**: worth keeping (protected, or with a capability that neither a native feature (main-job test) nor another installed tool covers)
  but broken or not working as intended. Give the diagnosis and the fix,
  never removal.
- **Keep**: earns its place. One line each in the report.

A **ban** that names the item, in the user's CLAUDE.md or decisions file,
outranks all of these (see "Ban versus protection").

## Mode A: install gate

1. **Identify the exact target and its state.** Run `claude plugin list --json`
   and read `enabledPlugins` in all settings files: if the target is already
   installed, the request is really to enable or disable it at some scope.
   Find what it would add: skills, agents, commands, hooks (and whether they
   return `additionalContext` or fire on SessionStart, UserPromptSubmit or
   SubagentStart), MCP servers and their `instructions` text. Read its files
   without running any of them: first the local marketplace copy under
   `~/.claude/plugins/marketplaces/<marketplace>/`, otherwise
   `git clone --depth 1` into a temporary folder (for a marketplace entry
   pinned to a commit, `git init` there and `git fetch --depth 1 origin <sha>`,
   so you read the version that would be installed). Never run its installer,
   scripts, hooks or servers to find out what they do.
2. **Banned by name?** Refuse at once: quote the ban with its file and line,
   name the native feature that covers this extension's job, and do not
   install it even if asked again. Skip the research. If only a broad ban (a
   publisher, a marketplace) covers it, do step 3 first: if it is protected,
   quote both entries and ask; if it is not, refuse as above.
3. **History and protection.** Run history.py on the target. If it is
   protected (see "Protected items" above), install or enable it as asked, and
   only report notes, or the fix if it is broken.
4. **Research it** as [references/research.md](references/research.md)
   describes. Do not install anything while research is pending.
5. **Answer by verdict**, in the reply format below:
   - **Total garbage**: do not install. Give the two or three reasons that
     decide it with their evidence, and the native feature or better tool with
     how to use it ([references/native-counterparts.md](references/native-counterparts.md)).
     If nothing is needed in its place, say so instead of inventing a
     replacement. Install only if the user then says explicitly that they want
     it anyway: use the scope they asked for (if they named none, ask), and
     record the override in the decisions file.
   - **Questionable**: say what it is good for and what it costs, and offer to
     install it with the limit applied (the exact setting from
     [references/controls.md](references/controls.md)). If the user declines
     the limit, install it as they asked.
   - **Not useful at the moment**: say where it would be useful, and offer an
     install at that project's scope instead. If the user declines, install it
     as they asked.
   - **Fix**: go ahead as asked, and give the diagnosis and the exact fix
     steps.
   - **Keep**: go ahead with the install the user asked for.

Reply format for Mode A:

```
<target>: <verdict>.
What it adds: <components, from its files>.
Why: <two or three deciding reasons>.
Use instead: <native feature or better tool, how to invoke it> | Nothing is needed in its place.
Offer: <exact command for the install, limited install, or nothing>.
Fix: <diagnosis and exact steps, only for a broken item>.
Evidence: <URLs and path:line>
```

## Mode B: scan

1. **Inventory.** Inside a git repository, run from its root; outside one, or
   when the user asks for a global scan, from the home folder:

   ```bash
   python3 "$HOME/.claude/skills/skillqa/scripts/inventory.py" --text --out <scratch folder>/skillqa-inventory.json
   ```

   Use the session's scratch folder if it has one, otherwise a new temporary
   folder.

   It lists user, project, plugin and claude.ai-synced skills; installed and
   synced plugins with their components, hook events, context-injecting hooks,
   MCP servers and always-on token cost; marketplaces; MCP servers; the
   settings and deny rules that already limit anything; and Claude Code's usage
   counters. Each skill is marked `loaded_here` and with its `override`, so
   nothing already switched off gets recommended again. It prints no secrets.
   Read its `errors` first and inspect any failed part by hand.

   claude.ai connectors are not on disk: `claude_ai_connectors_ever_connected`
   is history, not the current set. Take the current connectors from the MCP
   servers named in this session's context (connected, failed or blocked), or
   ask the user for their `/mcp` list. Items only in the history are Not rated.
2. **Context.** Note the project (git root, stack, CLAUDE.md files) and the
   session's task, if there is one. Outside a project and with no task, do not
   use "Not useful at the moment".
3. **History.** Run history.py once with every candidate's names (bare names
   and ids, for example `ponytail ponytail@ponytail`; MCP server names; skill
   names and the plugin each belongs to) and read the
   memory notes it points to. Mark every item the user deliberately set up as
   protected, with the date and the user's own words as evidence. Do this
   before any verdict, and hand the result, plus the decisions file's
   Allowlist and ban entries verbatim, to every researcher.
4. **First pass from the files.** For each candidate, write down what it
   actually adds and does (from its code and SKILL.md, not its marketing),
   which native feature overlaps, its per-session cost, conflicts with the
   user's instructions or other extensions, and its usage counter. If this
   Claude Code version has `/skill-doctor`, ask the user to run it and use its
   cost and usage report as evidence too. Built-in Claude Code skills and
   plugins are the native counterparts, not candidates. claude.ai connectors,
   synced plugins and synced skills are candidates.
5. **Validate by research.** Every rated item gets the research in
   [references/research.md](references/research.md), with at least one source
   about the item itself (its repository, issues, marketplace page, or "no
   public footprint" and the searches tried). The only exception is an item
   the decisions file already records as Keep. Run one researcher per item or
   per small group of similar items, in parallel: a workflow when the user has
   opted into workflows (ultracode), subagents otherwise. Give every
   researcher the history result, the decisions file's Allowlist and ban
   entries, and the full session id (`${CLAUDE_SESSION_ID}`) in case they run
   history.py themselves, and have them check their verdicts against all of
   it. No verdict goes in the report without its
   evidence.
6. **Check before reporting.** Go through the draft once more: no protected
   item appears in Total garbage, Questionable or Not useful at the moment,
   and no offer touches a protected item except to carry out its fix; every
   overlap claim passes the overlap rules below; every broken item that is
   protected or has a capability that neither a native feature (main-job test) nor another installed tool covers is in Fix; every
   item without history either shows no sign of deliberate setup or has been
   asked about.
7. **Report** in the format below.
8. **Offer the changes, then wait.** List every proposed change on its own
   line with what will be lost if it is applied; never hide a removal inside a
   batch. Protected items never appear in the offer except for their fixes.
   Change nothing until the user confirms, with one exception: an item named
   by a ban whose entry orders removal at once (its "If found installed" line
   in the decisions file, or the ban's own wording in a CLAUDE.md) is
   removed, then reported. For
   claude.ai-synced items, give the local setting, and say where to turn it
   off on claude.ai only if it is not useful in the other Claude products
   either (Cowork, the Chrome side panel, chat).

## Report format

```
skillqa scan: <project path, or "global">, <date>

Total garbage (remove now)
- <name> (<kind>, <source>, <scope>): <what it does or fails to do>.
  Use instead: <native feature or better tool, how to invoke it> | Nothing is needed in its place.
  Evidence: <URL or path:line>.  Remove: `<exact command>`

Questionable (limit it)
- <name>: <narrow use, mixed results, cost>.
  Recommendation: <exact usage>.  Set: `<setting or command>`.
  Evidence: <URL or path:line>

Not useful at the moment (<project>)
- <name>: <why not here, where it is useful>.
  Set: `<project-scope setting>` | No change needed: unused for this task.
  Evidence: <URL or path:line>

Fix (keep it; it is broken or not working as intended)
- <name>: <what is wrong, from evidence>.  Set up by: <date, the user's words> (if protected).
  Fix: <exact steps>.
  Evidence: <URL or path:line>

Keep
- <name>: <why it earns its place, in a few words>

Not rated: <anything skipped, and why>
```

Leave out an empty category. Keep each entry to three lines; a busy reader
should get each reason on the first read. Put anything longer under a short
"Notes" list after the report, and ask the questions that would change a
verdict at the end.

## Rules

- Usefulness and quality only. Do not repeat security findings.
- The allowlist above is absolute, except for a ban that names the item (see
  "Ban versus protection"): security tooling, anything the user deliberately
  set up, the user's own skills, and the decisions file's allowlist are never
  recommended for removal, disabling, denial or limiting.
- Broken is not useless. Diagnose why it fails and give the fix; recommend
  removal only for an unprotected item without a capability that neither a native feature (main-job test) nor another installed tool covers.
- Overlap rules. Against another installed extension, "X covers Y" needs
  proof for every capability: compare their actual tool or feature lists and
  name, for each thing Y does, the tool of X that does it; one uncovered
  capability means no overlap verdict. Against a native Claude Code feature,
  judge by Y's main job (small extras do not save it), but list every
  capability the native feature does not cover and show from history and
  usage that the user relies on none of them.
- Never run `claude mcp list` or `claude mcp get`, and never call an MCP
  server's tools to test it: that starts servers, and some open windows.
- Never execute an extension's code to evaluate it. Read it.
- Total garbage is reserved for "does nothing useful" or "a native feature
  does its main job". Rarely used or narrow is Questionable or Not useful at
  the moment, never garbage.
- Judge for this user: their CLAUDE.md files, the decisions file and the
  current project. A ban that names the item is final.
- Count the cost of merely being installed: always-on tokens, hooks that
  inject text into every session, prompt or subagent, hooks on every tool
  call, MCP server instructions (they enter the system prompt of every session
  where the server is on), directives that compete with the user's ("you
  MUST", "use this instead of WebFetch, no exceptions"), telemetry, and files
  it writes into projects. `claude plugin details` works only on installed
  plugins and does not count hook-injected text; check the files.
- An author's own claims and benchmarks are weak evidence. Independent
  issues, reviews, benchmarks and the code itself are strong evidence.
- Usage counters are evidence, with a caveat: a hook that fires every session
  raises the count without the user ever choosing the extension.
- Do not rate skillqa itself.
- When the user accepts or overrides a verdict, add it to
  `~/.claude/skillqa/known-verdicts.md` (create it from the template) with the
  date, the scope, the reason and the setting that enforces it.

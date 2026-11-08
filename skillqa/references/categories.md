# Verdict categories

From mildest to most severe: Keep, Fix, Not useful at the moment,
Questionable, Total garbage. A ban that names the item outranks all of them.

## Protected items come first

Security tooling for extensions (skill-inspector, SkillSpector and the like),
anything the user deliberately set up (history.py shows they asked for it or a
session built it for them, including the hooks, services and profiles around
it), the user's own skills, and the decisions file's allowlist are rated only
Keep or Fix. They never get Total garbage, Questionable or Not useful at the
moment, and never appear in a removal offer. A broad request ("turn off what
is irrelevant here", "clean up", "remove what is unused") never covers a
protected item: carry it out for the rest, list the protected ones it would
have touched, and ask. Only a ban that names the item outranks protection.

"Covered elsewhere" always means: by a native feature under the main-job test
below, or by another installed extension under the every-capability test
(one matching tool named for each capability).

## Fix: keep it, it is broken

A protected item, or one with a capability that neither a native feature (main-job test) nor another installed tool covers,
that fails or does not work as intended. Give the diagnosis from evidence and
the exact fix. Example: a self-hosted crawler MCP server, set up by the user as
their local replacement for a paid service and the only installed tool that
crawls whole sites, failed because its container was not running when
sessions started; the fix was to run it as an always-on service, not to
remove it.

## Total garbage: remove now, do not use

Reserved for exactly two cases:

1. **It does nothing useful.** Reading its code shows it is empty or trivial,
   only works in another product (for example a skill that needs the desktop
   app's Cowork), only restates generic advice the model already follows, or
   is broken beyond repair, abandoned upstream, unprotected and with every
   capability covered elsewhere.
2. **A native Claude Code feature does its main job.** Name the feature and
   how to invoke it. Judge by what the extension is mainly installed for:
   small extras do not save it, but list every capability the native feature
   does not cover and show from history and usage that the user relies on
   none of them. If its main value is something no native feature offers, it
   is not garbage. This main-job test applies only to native features; overlap
   with another installed extension needs proof for every capability (see
   the tie-breakers).

Example: superpowers. Its multi-agent parts duplicate workflows (ultracode),
subagents and `/code-review`; its planning duplicates plan mode. Its few extra
skills (test-first, debugging discipline) do not change that, and its start-up
hook orders a skill check before every reply, which fights the user's own
instructions. Use ultracode instead.

Not garbage: rarely used, narrow, or only useful in other projects. Those go
below.

## Questionable: limit it

Narrow scope of use and mixed results, so it should not run by default. The
recommendation says exactly how to use it and which setting enforces that:

- **on demand only**: the user turns it on when they want it. For a plugin
  this means kept disabled and enabled only for that session, because Claude
  can load a plugin's skills on its own whenever the plugin is enabled, and
  `skillOverrides` cannot stop that; deny rules can
  (`permissions.deny: "Skill(<plugin>:<skill>)"` and
  `"Skill(<plugin>:<skill> *)"`). For a standalone skill,
  `skillOverrides` "user-invocable-only".
- **only in certain projects**: enabled at project scope there;
- **only part of it**: deny the skills or tools that duplicate native
  features.

Example: ponytail. The author's own benchmark shows savings on short
greenfield tasks and little on surgical fixes in existing code. Its hooks
inject rules into every session, prompt and subagent, it conflicts with
ultracode, and its task board writes files after every turn even in its "off"
mode. Recommendation: keep it disabled; when you want it, run
`claude plugin enable ponytail@ponytail --scope user`, start a new session (or
run `/reload-plugins`), type `/ponytail full`, and disable it again afterwards
with `--scope user`.

Also Questionable: useful but costly in context (say the cheaper way to keep
it), if the item is not protected. Broken and worth keeping is Fix, not
Questionable.

## Not useful at the moment

A reasonable extension with no use in the current project or task. Only rate
this inside a project (a git repository) or when the session has a clear task;
in a global scan with no project, skip this category.

The recommendation is a scope: disable it for this project only
(`enabledPlugins` false in `.claude/settings.local.json`, a `skillOverrides`
entry, or `/mcp` per-project disable), and keep it where it helps. When it is
only irrelevant to this session's task, say that no change is needed.

Example: frontend-design (web UI design guidance) in a C++/QML desktop
widget project.

## Keep

Earns its place in this context. One line each in the report, so the scan
reads as complete.

## Tie-breakers

Apply these in order; the first that fits decides.

1. **A ban that names it**: as the ban says.
2. **Protected**: Keep, or Fix when broken. Nothing else. If a broad ban
   (publisher, marketplace) also covers it, change nothing and ask.
3. **A native feature does its main job** (main-job test above): Total
   garbage, even if it is broken or was never set up.
4. **Broken or never set up**, with a capability that neither a native
   feature nor any other installed tool provides: Fix, with the repair or
   setup steps.
5. **Every capability proven covered** by other installed tools (one
   matching tool named per capability): Questionable, recommending which of
   the overlapping tools to keep and why (cost, reliability).
6. **Works, and its main value is something nothing else provides**: Keep if
   it is broad and cheap; Questionable if its use is narrow, its results mixed
   or its cost high.
7. **Fine, but not for this project or task**: Not useful at the moment.
8. **Zero uses over many sessions** is evidence for 5 to 7, never a verdict
   on its own.
9. **Overrides the user's instructions** (start-up mandates, "you MUST" or
   "no exceptions" text that conflicts with CLAUDE.md): count it heavily
   against the extension.
10. **Still unsure** after research: pick the milder verdict and say what
    evidence would settle it; for an item without history that may have been
    set up on purpose, ask the user.

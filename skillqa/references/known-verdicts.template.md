# Known verdicts

Template for `~/.claude/skillqa/known-verdicts.md`, where skillqa keeps the
user's standing decisions. The file lives outside this repository because it
is personal and because skillqa adds to it over time. skillqa applies these
decisions before any research of its own.

An "Allowlist" section lists items that skillqa must never recommend for
removal, disabling, denial or limiting, one line each with the reason:

## Allowlist

- <name, id or group, and everything built around it>: <why: security
  tooling, set up deliberately on <date>, the user's own work>.

Then one section per other decision:

## <name> (`<plugin id, skill name or MCP server>`): <verdict or "banned">

- **Date and scope:** <YYYY-MM-DD>; <all projects, one project, or every
  system the user runs Claude Code on>.
- **Verdict:** <Total garbage, Questionable, Not useful at the moment, Fix,
  Keep, or banned>. A ban means: refuse outright, even if asked again.
- **If found installed:** <remove at once and report, or report and ask>
  (bans only; without this line, skillqa reports and asks).
- **Covers:** <ids, marketplaces, skill prefixes, publishers, when more than
  one item>.
- **Reason:** <the deciding facts, with sources>.
- **Recommendation / enforced by:** <the exact setting or CLAUDE.md section>.
- **Use instead:** <native feature or better tool, if any>.

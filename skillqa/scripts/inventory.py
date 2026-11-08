#!/usr/bin/env python3
"""Read-only inventory of everything that extends Claude Code on this machine.

    python3 inventory.py [--project DIR] [--no-details] [--text] [--out FILE]

Prints JSON (or a short text summary with --text): project context, skills
(user, project, plugin, claude.ai-synced), plugins and synced plugins with
their components, hook events and always-on token cost, marketplaces, MCP
servers, the settings that already limit any of them, and the usage counters
Claude Code keeps. Any part that fails is named under "errors".

    --out FILE     write the JSON to FILE (with --text, print the summary too)
    --self-test    check the secret filters and exit

It reads files and runs only `git rev-parse`, `git ls-files`,
`claude plugin list --json` and `claude plugin details <id>`. From MCP server
definitions and server allow/deny rules it prints only names, types, URL
hosts and a package or script name that passes strict shape checks; never
environment values, headers, flag values or anything shaped like a key.
"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOME = Path.home()
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
args = sys.argv[1:]


def opt(name):
    if name not in args:
        return None
    i = args.index(name)
    if i + 1 >= len(args) or args[i + 1].startswith("--"):
        sys.exit(f"inventory.py: {name} needs a value")
    return args[i + 1]


PROJECT = Path(opt("--project") or Path.cwd()).resolve()
if not PROJECT.is_dir():
    sys.exit(f"inventory.py: --project {PROJECT} is not a folder")
OUT = opt("--out")
DETAILS = "--no-details" not in args
ERRORS = []

# Hook events whose output Claude Code adds to the model's context.
CONTEXT_EVENTS = {"SessionStart", "UserPromptSubmit", "UserPromptExpansion", "PostModelSwitch", "SubagentStart"}


def load_json(path, label=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        if label:
            ERRORS.append(f"{label}: could not read {path}: {e.__class__.__name__}")
        return None


def run(cmd, timeout=60):
    if cmd[0] in ("claude", "git"):  # resolves claude.exe, an npm claude.cmd shim, git.exe
        cmd = [shutil.which(cmd[0]) or cmd[0], *cmd[1:]]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=PROJECT)
    except (OSError, subprocess.TimeoutExpired) as e:
        return None, f"{' '.join(cmd[:3])}: {e.__class__.__name__}"
    if out.returncode != 0:
        return None, f"{' '.join(cmd[:3])}: exit {out.returncode}: {out.stderr.strip()[:200]}"
    return out.stdout, None


def frontmatter(skill_md):
    """name, description and invocation flags from a SKILL.md header."""
    try:
        text = Path(skill_md).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    info = {"lines": text.count("\n") + 1}
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    if not m:
        return info
    head = m.group(1)
    for key in ("name", "description", "disable-model-invocation", "user-invocable"):
        km = re.search(rf"^{re.escape(key)}:\s*(.*?)(?=^\S[\w-]*:|\Z)", head, re.S | re.M)
        if km:
            val = " ".join(line.strip() for line in km.group(1).strip().splitlines())
            info[key] = val.strip(">|- ").strip("\"'")
    return info


def skills_in(root, source, pattern="*/SKILL.md", prefix=""):
    """Skills at the documented depth only. glob, unlike rglob, follows symlinked skill folders."""
    root = Path(root)
    found = []
    if not root.is_dir():
        return found
    for skill_md in sorted(root.glob(pattern)):
        if source == "user" and skill_md.relative_to(root).parts[0] == "synced":
            continue  # listed separately
        fm = frontmatter(skill_md)
        name = fm.get("name") or skill_md.parent.name
        found.append({
            "name": prefix + name,
            "source": source,
            "path": str(skill_md.parent),
            "symlink": skill_md.parent.is_symlink(),
            "description": (fm.get("description") or "")[:400],
            "lines": fm.get("lines"),
            "disable_model_invocation": fm.get("disable-model-invocation"),
            "user_invocable": fm.get("user-invocable"),
        })
    return found


def git_root(path):
    out, _ = run(["git", "-C", str(path), "rev-parse", "--show-toplevel"], timeout=10)
    return out.strip() if out else None


MARKERS = {
    "CMakeLists.txt": "C/C++ (CMake)", "meson.build": "C/C++ (Meson)", "Makefile": "make",
    "package.json": "JavaScript/TypeScript", "pyproject.toml": "Python", "requirements.txt": "Python",
    "Cargo.toml": "Rust", "go.mod": "Go", "pom.xml": "Java (Maven)", "build.gradle": "JVM (Gradle)",
    "Gemfile": "Ruby", "composer.json": "PHP", ".csproj": ".NET", "pubspec.yaml": "Dart/Flutter",
    "Dockerfile": "Docker", "metadata.json": "metadata.json (Plasma, GNOME or other extension package?)",
}


def project_context():
    root = git_root(PROJECT)
    stack, top = set(), []
    if root:
        listing, err = run(["git", "-C", root, "ls-files"], timeout=30)
        if err:
            ERRORS.append(f"project files: {err}")
        files = (listing or "").splitlines()
        exts = {}
        for f in files:  # tracked files only, so build output does not count
            base = os.path.basename(f)
            for marker, label in MARKERS.items():
                if base == marker or (marker.startswith(".") and base.endswith(marker)):
                    if f.count("/") <= 1:
                        stack.add(label)
            ext = os.path.splitext(f)[1].lower()
            if ext:
                exts[ext] = exts.get(ext, 0) + 1
        top = sorted(exts.items(), key=lambda kv: -kv[1])[:10]
    base = Path(root) if root else PROJECT
    return {
        "cwd": str(PROJECT),
        "git_root": root,
        "in_project": bool(root),
        "stack_markers": sorted(stack),
        "top_file_types": top,
        "claude_md_files": [str(p) for p in (base / "CLAUDE.md", base / ".claude" / "CLAUDE.md", base / "CLAUDE.local.md") if root and p.exists()],
    }


def hook_events(folder, manifest):
    """Hook events from hooks/hooks.json and wherever the manifest's "hooks" points (path, list or inline)."""
    declared = manifest.get("hooks")
    sources = [folder / "hooks" / "hooks.json"]
    if isinstance(declared, str):
        sources.append(folder / declared)
    elif isinstance(declared, list):
        sources += [folder / d for d in declared if isinstance(d, str)]
    maps = [load_json(s) for s in dict.fromkeys(sources)]
    if isinstance(declared, dict):
        maps.append(declared)
    events = {}
    for hm in maps:
        if not isinstance(hm, dict):
            continue
        for event, entries in (hm.get("hooks", hm) or {}).items():
            if not isinstance(entries, list):
                continue
            ev = events.setdefault(event, {"matchers": set(), "types": set()})
            for e in entries:
                if isinstance(e, dict):
                    ev["matchers"].add(e.get("matcher", "*"))
                    for h in e.get("hooks", []) if isinstance(e.get("hooks"), list) else []:
                        if isinstance(h, dict):
                            ev["types"].add(h.get("type", "command"))
    return [{"event": k, "matchers": sorted(v["matchers"]), "types": sorted(v["types"]),
             "may_inject_context": k in CONTEXT_EVENTS or bool(v["types"] & {"prompt", "agent"})}
            for k, v in events.items()]


def plugin_components(folder):
    p = Path(folder or "")
    comp = {"skills": [], "agents": [], "commands": [], "hooks": [], "mcp_servers": [], "hook_files_injecting_context": []}
    if not p.is_dir():
        return comp
    manifest = load_json(p / ".claude-plugin" / "plugin.json") or {}
    comp["skills"] = sorted({s.parent.name for s in p.glob("skills/*/SKILL.md")})
    comp["agents"] = sorted(a.stem for a in p.glob("agents/*.md"))
    comp["commands"] = sorted(c.stem for c in p.glob("commands/**/*.md"))
    comp["hooks"] = hook_events(p, manifest)
    # Files that return additionalContext put text into the model's context; plugin details does not count it.
    if comp["hooks"]:
        for f in list(p.glob("hooks/**/*"))[:300]:
            try:
                if f.is_file() and f.stat().st_size < 2_000_000 and "additionalContext" in f.read_text(encoding="utf-8", errors="ignore"):
                    comp["hook_files_injecting_context"].append(str(f.relative_to(p)))
            except OSError:
                pass
    mcp = load_json(p / ".mcp.json") or {}
    servers = dict(mcp.get("mcpServers", mcp) if isinstance(mcp, dict) else {})
    if isinstance(manifest.get("mcpServers"), dict):
        servers.update(manifest["mcpServers"])
    comp["mcp_servers"] = sorted(servers)
    meta = {k: manifest.get(k) for k in ("name", "version", "description", "homepage", "repository") if manifest.get(k)}
    author = manifest.get("author")
    if author:
        meta["author"] = author.get("name") if isinstance(author, dict) else author
    comp["manifest"] = meta
    return comp


def always_on_tokens(plugin_id):
    out, err = run(["claude", "plugin", "details", plugin_id], timeout=60)
    if err:
        ERRORS.append(f"plugin details {plugin_id}: {err}")
        return None
    m = re.search(r"Always-on:\s*~?([\d.,]+)\s*(k?)\s*tok", out)
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return int(n * 1000) if m.group(2) else int(n)


def plugins():
    listed, err = run(["claude", "plugin", "list", "--json"])
    if err:
        ERRORS.append(f"plugin list: {err}")
        return []
    try:
        items = json.loads(listed)
    except ValueError:
        ERRORS.append("plugin list: output was not JSON")
        return []
    result = []
    for it in items:
        entry = {k: it.get(k) for k in ("id", "version", "scope", "enabled", "projectEnabled", "installPath", "installedAt", "lastUpdated")}
        entry.update(plugin_components(it.get("installPath")))
        if DETAILS:
            entry["always_on_tokens"] = always_on_tokens(it["id"])
        result.append(entry)
    return result


def synced_plugins(loaded_ids):
    """claude.ai-synced plugins as stored on disk, whether or not this folder loads them."""
    out = []
    for manifest in sorted((CLAUDE / "plugins" / "synced").glob("*/manifest.json")):
        data = load_json(manifest, "synced plugins") or {}
        for pl in data.get("plugins", []):
            name = pl.get("name")
            folder = next((f for f in [manifest.parent / name, *sorted(manifest.parent.glob(f"{name}~g*"))] if f.is_dir()), None)
            entry = {
                "id": f"{name}@synced",
                "loaded_here": f"{name}@synced" in loaded_ids,
                "description": (pl.get("description") or "")[:300],
                "marketplace": pl.get("marketplaceName"),
                "installation_preference": pl.get("installationPreference"),
                "updated": pl.get("updatedAt"),
                "path": str(folder) if folder else None,
            }
            entry.update(plugin_components(folder))
            out.append(entry)
    return out


# What may be printed from an MCP server definition: a package or script name, a URL host.
PACKAGE = re.compile(r"^(@[a-z0-9][a-z0-9._-]*/)?[a-z0-9][a-z0-9._-]*(@[a-z0-9._^~-]+)?$")
SCRIPT = re.compile(r"^[\w.-]+\.(js|mjs|cjs|ts|py|sh)$")
KEY_PREFIX = re.compile(r"(?i)(^|[^a-z])(sk-|sk_|pk_|rk_|xox[abprs]-|ghp_|gho_|ghs_|ghu_|github_pat_|glpat-|akia|aiza|hf_|eyj)")
UUID = re.compile(r"(?i)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SECRET_WORD = re.compile(r"(?i)token|secret|passw|apikey|api_key|bearer|credential")


def looks_secret(text):
    mixed_runs = [r for r in re.findall(r"[A-Za-z0-9]{8,}", text) if re.search(r"[A-Za-z]", r) and re.search(r"\d", r)]
    return bool(KEY_PREFIX.search(text) or UUID.search(text) or SECRET_WORD.search(text) or mixed_runs)


def package_hint(argv):
    """The first argument shaped like a package or script name; anything else, flag values included, is never printed."""
    for a in map(str, argv):
        if a.startswith("-"):
            continue
        for cand in (a, os.path.basename(a.rstrip("/"))):
            if (PACKAGE.match(cand) or SCRIPT.match(cand)) and len(cand) <= 80 and not looks_secret(cand):
                return cand
    return None


def url_host(url):
    """scheme://host[:port] only: user info, path, query and fragment are dropped."""
    m = re.match(r"^([a-zA-Z][\w+.-]*)://(.*)$", str(url))
    if not m:
        return None
    rest = m.group(2)
    if "@" in rest:
        rest = rest[rest.rindex("@") + 1:]
    host = re.split(r"[/?#]", rest, maxsplit=1)[0]
    return f"{m.group(1)}://{host}" if re.fullmatch(r"[\w.-]+(:\d+)?|\[[0-9a-fA-F:.]+\](:\d+)?", host) else None


def safe_server(name, spec, where):
    spec = spec if isinstance(spec, dict) else {}
    out = {"name": name, "where": where, "type": spec.get("type") or ("http" if spec.get("url") else "stdio")}
    if spec.get("command"):
        out["command"] = os.path.basename(str(spec["command"]))
        hint = package_hint(spec.get("args", []))
        if hint:
            out["package_hint"] = hint
    if spec.get("url"):
        out["url_host"] = url_host(spec["url"])
    if "alwaysLoad" in spec:
        out["alwaysLoad"] = spec["alwaysLoad"]
    return out


def safe_server_rule(rule):
    """An allowedMcpServers / deniedMcpServers entry without command arguments or URL secrets."""
    if not isinstance(rule, dict):
        return rule if isinstance(rule, str) else None
    out = {}
    if "serverName" in rule:
        out["serverName"] = rule["serverName"]
    if "serverUrl" in rule:
        out["serverUrl_host"] = url_host(rule["serverUrl"])
    if isinstance(rule.get("serverCommand"), list) and rule["serverCommand"]:
        out["serverCommand"] = os.path.basename(str(rule["serverCommand"][0]))
    return out


def self_test():
    cases = {
        ("npx", "--yes", "some-mcp", "sk-proj-abcDEF123ghi"): "some-mcp",
        ("npx", "-y", "@playwright/mcp@latest", "--headless", "--executable-path", "/opt/brave"): "@playwright/mcp@latest",
        ("npx", "--token", "abcSECRET9x", "some-mcp"): "some-mcp",
        ("openai-mcp", "sk-" + "a1" * 24): None,
        ("slack-mcp", "xoxb-1234-5678-abcdef"): None,
        ("mcp-proxy", "-k", "hunter2abc", "server"): "server",
        ("node", "/opt/tools/browser-mcp/mcp.js", "--browser", "brave"): "mcp.js",
        ("srv", "123e4567-e89b-12d3-a456-426614174000"): None,
    }
    for argv, want in cases.items():
        got = package_hint(argv[1:])
        assert got == want, f"package_hint{argv[1:]} = {got!r}, wanted {want!r}"
    urls = {
        "https://admin:s3cr?t@host.example/mcp": "https://host.example",
        "https://user:p@ss@host.example/x": "https://host.example",
        "https://u:a/b@host.example/x": "https://host.example",
        "https://host.example:8443/mcp?token=zzz": "https://host.example:8443",
        "http://127.0.0.1:11235/mcp/sse": "http://127.0.0.1:11235",
    }
    for u, want in urls.items():
        got = url_host(u)
        assert got == want, f"url_host({u!r}) = {got!r}, wanted {want!r}"
    assert safe_server_rule({"serverCommand": ["npx", "x", "TOKEN123abc"], "serverUrl": "https://u:p@h.example/?k=1"}) == {"serverUrl_host": "https://h.example", "serverCommand": "npx"}
    print("self-test passed")


def mcp_servers(root):
    cfg = load_json(HOME / ".claude.json", "~/.claude.json") or {}
    servers = [safe_server(n, s, "user (~/.claude.json)") for n, s in (cfg.get("mcpServers") or {}).items()]
    projects = cfg.get("projects") or {}
    proj = {}
    if root:  # Claude Code stores project keys with / or \ on Windows
        for key in (root, root.replace("/", "\\"), root.replace("\\", "/")):
            if key in projects:
                proj = projects[key]
                break
    servers += [safe_server(n, s, "local (this project, ~/.claude.json)") for n, s in (proj.get("mcpServers") or {}).items()]
    if root:
        mcpjson = load_json(Path(root) / ".mcp.json", ".mcp.json") or {}
        servers += [safe_server(n, s, "project (.mcp.json)") for n, s in (mcpjson.get("mcpServers") or {}).items()]
    return {
        "configured": servers,
        "disabled_in_this_project": proj.get("disabledMcpServers"),
        "enabled_in_this_project": proj.get("enabledMcpServers"),
        "rejected_mcpjson_servers": proj.get("disabledMcpjsonServers"),
        "claude_ai_connectors_ever_connected": cfg.get("claudeAiMcpEverConnected"),
        "mcp_auth_notices_seen": cfg.get("mcpNeedsAuthNoticed"),
        "note": "claude_ai_connectors_ever_connected and mcp_auth_notices_seen are history lists, not the current state; take the current connectors from the session's MCP server list or /mcp. Plugin MCP servers are listed under each plugin.",
    }


def settings_controls(root):
    files = {"managed": Path("/etc/claude-code/managed-settings.json"), "user": CLAUDE / "settings.json"}
    if root:
        files["project"] = Path(root) / ".claude" / "settings.json"
        files["local"] = Path(root) / ".claude" / "settings.local.json"
    keys = ("enabledPlugins", "skillOverrides", "disabledMcpjsonServers", "enabledMcpjsonServers", "enableAllProjectMcpServers",
            "syncClaudeAiSkills", "syncClaudeAiPlugins", "disableClaudeAiConnectors", "disableBundledSkills", "disableAllHooks",
            "skillListingBudgetFraction", "skillListingMaxDescChars")
    out = {}
    for scope, f in files.items():
        data = load_json(f, f"{scope} settings")
        if data is None:
            continue
        sel = {k: data[k] for k in keys if k in data}
        for k in ("deniedMcpServers", "allowedMcpServers"):  # entries can hold commands or URLs: keep names and hosts only
            if isinstance(data.get(k), list):
                sel[k] = [safe_server_rule(r) for r in data[k]]
        if data.get("extraKnownMarketplaces"):
            sel["extraKnownMarketplaces"] = sorted(data["extraKnownMarketplaces"])
        deny = [d for d in (data.get("permissions") or {}).get("deny", []) if isinstance(d, str) and (d.startswith("Skill") or d.startswith("mcp__"))]
        if deny:
            sel["deny_rules"] = deny
        if data.get("env"):
            sel["env_keys"] = sorted(data["env"])  # names only, never values
        hooks = data.get("hooks") or {}
        if hooks:
            sel["hooks"] = [{"event": ev, "matchers": sorted({e.get("matcher", "*") for e in entries if isinstance(e, dict)})}
                            for ev, entries in hooks.items() if isinstance(entries, list)]
        out[scope] = {"file": str(f), **sel}
    return out


def usage():
    cfg = load_json(HOME / ".claude.json") or {}
    return {
        "numStartups": cfg.get("numStartups"),
        "skillUsage": cfg.get("skillUsage"),
        "pluginUsage": cfg.get("pluginUsage"),
        "note": "usageCount counts invocations Claude Code recorded; a plugin whose hooks fire every session can show a high count without the user ever choosing it. lastUsedAt is epoch milliseconds.",
    }


def effective(settings, key):
    """The value of a settings key as Claude Code resolves it: local over project over user (managed wins)."""
    for scope in ("managed", "local", "project", "user"):
        if key in settings.get(scope, {}):
            if key in ("syncClaudeAiSkills", "syncClaudeAiPlugins") and scope == "project":
                continue  # not read from .claude/settings.json
            return settings[scope][key]
    return None


def mark_skills(skill_list, settings, plugin_list):
    overrides = {}
    for scope in ("user", "project", "local", "managed"):  # later scopes win per key
        overrides.update(settings.get(scope, {}).get("skillOverrides") or {})
    sync_skills = effective(settings, "syncClaudeAiSkills")
    enabled_here = {p["id"]: bool(p.get("projectEnabled", p.get("enabled"))) for p in plugin_list}
    for s in skill_list:
        src = s["source"]
        if src.startswith("plugin "):
            s["loaded_here"] = enabled_here.get(src[len("plugin "):], False)
            continue  # skillOverrides does not apply to plugin skills
        bare = s["name"].split(":", 1)[-1]
        s["override"] = overrides.get(s["name"], overrides.get(bare))
        s["loaded_here"] = not (s["override"] == "off" or (src == "claude.ai-synced" and sync_skills is False))


def main():
    if "--self-test" in args:
        self_test()
        return
    ctx = project_context()
    root = ctx["git_root"]
    skill_list = skills_in(CLAUDE / "skills", "user")
    skill_list += skills_in(CLAUDE / "skills" / "synced", "claude.ai-synced", "*/*/SKILL.md", "anthropic-skills:")
    if root:
        skill_list += skills_in(Path(root) / ".claude" / "skills", "project")
    plugin_list = plugins()
    loaded = {p["id"] for p in plugin_list}
    synced = synced_plugins(loaded)
    for p in plugin_list + [s for s in synced if not s["loaded_here"]]:
        base = p.get("installPath") or p.get("path") or ""
        for s in p.get("skills", []):
            skill_list.append({"name": f"{p['id'].split('@')[0]}:{s}", "source": f"plugin {p['id']}", "path": str(Path(base) / "skills" / s)})
    data = {
        "errors": ERRORS,
        "context": ctx,
        "skills": skill_list,
        "plugins": plugin_list,
        "synced_plugins": synced,
        "marketplaces": sorted((load_json(CLAUDE / "plugins" / "known_marketplaces.json", "marketplaces") or {}).keys()),
        "mcp": mcp_servers(root),
        "settings": settings_controls(root),
        "usage": usage(),
    }
    mark_skills(skill_list, data["settings"], plugin_list)
    if OUT:
        Path(OUT).write_text(json.dumps(data, indent=2, default=str) + "\n", encoding="utf-8")
    if "--text" not in args:
        if not OUT:
            json.dump(data, sys.stdout, indent=2, default=str)
            print()
        return
    for e in ERRORS:
        print(f"ERROR {e}")
    c = data["context"]
    print(f"project: {c['git_root'] or 'none (not in a git repo)'}  stack: {', '.join(c['stack_markers']) or '-'}")
    print(f"skills: {sum(s['loaded_here'] for s in skill_list)} loaded here, {len(skill_list)} on disk  plugins: {len(plugin_list)} (+{sum(not s['loaded_here'] for s in synced)} synced not loaded here)  "
          f"marketplaces: {len(data['marketplaces'])}  mcp servers: {len(data['mcp']['configured'])}")
    for p in plugin_list + [s for s in synced if not s["loaded_here"]]:
        hooks = ",".join(h["event"] for h in p.get("hooks", []))
        inject = " INJECTS-CONTEXT" if p.get("hook_files_injecting_context") or any(h["may_inject_context"] for h in p.get("hooks", [])) else ""
        state = f"enabled={p.get('enabled')}" if "enabled" in p else "not loaded here"
        print(f"  plugin {p['id']:<48} {state} always-on~{p.get('always_on_tokens')} hooks=[{hooks}]{inject} "
              f"skills={len(p.get('skills', []))} mcp={len(p.get('mcp_servers', []))}")
    for s in skill_list:
        if not s["source"].startswith("plugin"):
            marks = (" (symlink)" if s.get("symlink") else "") + (f" override={s['override']}" if s.get("override") else "") + ("" if s["loaded_here"] else " NOT LOADED HERE")
            print(f"  skill  {s['name']:<48} {s['source']}{marks}")
    for m in data["mcp"]["configured"]:
        print(f"  mcp    {m['name']:<48} {m['where']}{'  ' + m['package_hint'] if m.get('package_hint') else ''}")


if __name__ == "__main__":
    main()

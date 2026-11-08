#!/usr/bin/env python3
"""Find what the user and past Claude Code sessions said about an extension.

    python3 history.py TERM [TERM ...] [--current-session ID] [--limit N]
    python3 history.py --self-test

For each term it searches every transcript under ~/.claude/projects/ (all
projects, all sessions), the memory notes, the CLAUDE.md files, skillqa's
decisions file and the hook scripts, and prints:

- USER: what the user typed in an interactive session (the strongest evidence),
- PROMPT: prompts of non-interactive runs (`claude -p`), which Claude itself
  may have written for tests,
- SETUP: commands sessions ran and files they wrote or edited for it,
- REPORTED: what sessions said they did,
- NOTE: lines in memory notes, CLAUDE.md files, the decisions file and hooks.

--current-session ID keeps the user's messages from the running session (their
latest corrections count) but drops its assistant text and commands, which
would only echo the review in progress.

No hits proves nothing: transcripts are deleted after cleanupPeriodDays, and
sessions on other machines are not here.

It reads files only. Of tool output it reads only the user's answers to
Claude's questions and the reasons they gave when rejecting a tool call. It
masks anything shaped like a key, token or password before cutting text to
length.
"""
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOME = Path.home()
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR", HOME / ".claude"))
SETUP = re.compile(r"(?i)\b(install|add-json|mcp add|marketplace add|enable|disable|remove|uninstall|podman|docker|systemctl|quadlet|uv tool|pip install|npm i|npx|git clone|ln -s)\b")
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
NOT_TYPED = ("<system-reminder>", "<local-command", "<command-message>", "<task-notification>", "[Request interrupted")
SECRET = re.compile(
    r"(?i)(bearer\s+)\S+|"
    r"((?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|access[_-]?key)[\w-]*[\"']?\s*[:=]\s*)\"[^\"\n]*\"|"
    r"((?:token|secret|password|passwd|pwd|api[_-]?key|private[_-]?key|access[_-]?key|authorization)[\w-]*[\"']?\s*[:=]\s*[\"']?(?:(?:bearer|basic)\s+)?)[^\s\"',}]+|"
    r"((?:secret[_-]?access[_-]?key|private[_-]?key)\s+)\S+|"
    r"(--?(?:token|password|passwd|secret|api[_-]?key)\s+)\S+|"
    r"((?:-u|--user)[=\s]+[^\s:]+:)\S+|"
    r"(sshpass\s+-p\s*)\S+|"
    r"(\s-p)(?=[^\s-])\S{4,}|"
    r"(://[^\s/:@]+:)[^\s@/]+(?=@)|"
    r"(?P<pfx>\b(?:sk-|sk_|pk_|rk_|xox[abprs]-|ghp_|gho_|ghs_|ghu_|github_pat_|glpat-|AKIA|AIza|hf_|eyJ)[\w./+-]{6,})|"
    r"\b(?=[A-Za-z0-9_-]{24,}\b)(?=[A-Za-z0-9_-]*\d)(?=[A-Za-z0-9_-]*[A-Za-z])[A-Za-z0-9_-]+\b")
TERMS = []  # set in main(); names that must never be masked


def mask(text):
    pfx = SECRET.groupindex["pfx"]

    def repl(m):
        for g in range(1, pfx):  # groups that keep their prefix (the key name, the flag)
            if m.group(g):
                return m.group(g) + "[masked]"
        if m.group("pfx"):  # a known key prefix is always a secret, whatever is searched for
            return "[masked]"
        word = m.group(0)
        if "__" in word or any(term_regex(t).match(word) for t in TERMS):  # tool and extension names
            return word
        return "[masked]"
    return SECRET.sub(repl, text)


def term_regex(term):
    parts = [re.escape(p) for p in re.split(r"[\s_-]+", term) if p]
    return re.compile(r"(?<![a-z0-9])" + r"[\s_-]*".join(parts) + r"(?![a-z0-9])", re.I)


def snippet(text, rx, width=240):
    t = mask(" ".join(text.split()))  # mask first, then cut, so a cut never exposes half a secret
    m = rx.search(t)
    i = m.start() if m else 0
    start = max(0, i - width // 2)
    return ("…" if start else "") + t[start:start + width] + ("…" if start + width < len(t) else "")


def project_name(entry, folder):
    cwd = entry.get("cwd")
    if cwd:
        return cwd.replace(str(HOME), "~", 1)
    prefix = str(HOME).replace("/", "-")
    return folder.name.replace(prefix, "~", 1)


def blocks(message):
    content = message.get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    return [b for b in content or [] if isinstance(b, dict)]


def add(found, t, bucket, entry, session):
    found[t][bucket].append(entry)
    found[t]["sessions"].add(session)


def search(terms, current, limit):
    rx = {t: term_regex(t) for t in terms}
    first = {t: re.split(r"[\s_-]+", t)[0] for t in terms}  # cheap prefilter
    found = {t: {k: [] for k in ("user", "prompt", "setup", "reported")} | {"sessions": set()} for t in terms}
    cwds = set()
    files = [f for f in sorted((CLAUDE / "projects").glob("*/**/*.jsonl")) if f.name != "journal.jsonl"]
    for f in files:
        rel = f.relative_to(CLAUDE / "projects").parts  # <project>/<session>.jsonl or <project>/<session>/subagents/...
        delegated = "subagents" in rel  # a subagent or workflow agent: its "user" text came from Claude
        session = rel[1] if delegated else f.stem
        is_current = bool(current) and session.startswith(current)
        if is_current and delegated:
            continue  # the running review's own agents only echo it
        ask_ids = set()
        try:
            lines = f.open(encoding="utf-8", errors="replace")
        except OSError:
            continue
        with lines:
            for line in lines:
                low = line.lower()
                if '"cwd"' in line and not delegated:
                    m = re.search(r'"cwd":"((?:[^"\\]|\\.)+)"', line)
                    if m:
                        try:
                            cwds.add(json.loads('"' + m.group(1) + '"'))  # undo JSON escaping (C:\\Users on Windows)
                        except ValueError:
                            pass
                if '"AskUserQuestion"' in line:
                    try:
                        for blk in blocks(json.loads(line).get("message") or {}):
                            if blk.get("type") == "tool_use" and blk.get("name") == "AskUserQuestion":
                                ask_ids.add(blk.get("id"))
                    except (ValueError, AttributeError):
                        pass
                cand = [t for t in terms if first[t] in low]
                if not cand:
                    continue
                try:
                    o = json.loads(line)
                except ValueError:
                    continue
                kind = o.get("type")
                when = (o.get("timestamp") or "")[:16].replace("T", " ")
                proj, sess = project_name(o, f.parent), session[:8]
                if kind == "attachment":  # messages the user typed while Claude was working
                    att = o.get("attachment") or {}
                    text = att.get("prompt") if att.get("type") == "queued_command" else None
                    if isinstance(text, str) and not text.lstrip().startswith(NOT_TYPED) and not delegated:
                        for t in cand:
                            if rx[t].search(text):
                                add(found, t, "user", (when, proj, sess, snippet(text, rx[t])), session)
                    continue
                msg = o.get("message") or {}
                if kind not in ("user", "assistant") or not isinstance(msg, dict):
                    continue
                if o.get("isMeta") or o.get("isCompactSummary"):
                    continue
                if is_current and kind == "assistant":
                    continue
                sidechain = delegated or o.get("isSidechain")
                for blk in blocks(msg):
                    btype = blk.get("type")
                    if btype == "text":
                        text = blk.get("text") or ""
                        if kind == "user" and text.lstrip().startswith(NOT_TYPED):
                            continue
                        if kind == "assistant":
                            bucket = "reported"
                        elif sidechain or str(o.get("entrypoint", "")).startswith("sdk"):
                            bucket = "prompt"
                        else:
                            bucket = "user"
                        for t in cand:
                            if rx[t].search(text):
                                add(found, t, bucket, (when, proj, sess, snippet(text, rx[t])), session)
                    elif btype == "tool_result" and kind == "user" and not sidechain:
                        c = blk.get("content")
                        text = c if isinstance(c, str) else " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
                        said = None
                        if blk.get("tool_use_id") in ask_ids:  # the user's answers to Claude's questions
                            pairs = re.findall(r'"((?:[^"\\]|\\.)*)"="((?:[^"\\]|\\.)*)"', text)
                            said = [("answered", a, q) for q, a in pairs] or [("answered", text, "")]
                        elif "the user said:" in text:  # the reason given when rejecting a tool call
                            said = [("rejected the call; said", text.split("the user said:", 1)[1], "")]
                        for label, answer, question in said or []:
                            for t in cand:
                                if rx[t].search(answer) or rx[t].search(question):
                                    q = f" (to: {mask(' '.join(question.split()))[:160]})" if question else ""
                                    add(found, t, "user", (when, proj, sess, f"{label}: {mask(' '.join(answer.split()))[:240]}{q}"), session)
                    elif btype == "tool_use" and kind == "assistant":
                        inp = blk.get("input") or {}
                        if blk.get("name") in WRITE_TOOLS:
                            path = str(inp.get("file_path") or inp.get("notebook_path") or "")
                            body = json.dumps(inp)
                            for t in cand:
                                if rx[t].search(path) or rx[t].search(body):
                                    add(found, t, "setup", (when, proj, sess, f"{blk['name']} {path}"), session)  # path only
                        else:
                            cmd = str(inp.get("command") or "")
                            for t in cand:
                                if rx[t].search(cmd) and SETUP.search(cmd):
                                    add(found, t, "setup", (when, proj, sess, mask(" ".join(cmd.split()))[:240]), session)
    notes = sorted((CLAUDE / "projects").glob("*/memory/*.md"))
    notes += [CLAUDE / "CLAUDE.md", CLAUDE / "skillqa" / "known-verdicts.md"] + sorted((CLAUDE / "rules").glob("*.md"))
    folders = set(HOME.glob("*/")) | {HOME}
    for d in cwds:
        p = Path(d)
        while True:  # a session folder and its parents up to home all contribute CLAUDE files
            folders.add(p)
            if p == HOME or p == p.parent or HOME not in p.parents:
                break
            p = p.parent
    for base in sorted(x for x in folders if x.is_dir()):
        notes += [base / "CLAUDE.md", base / "CLAUDE.local.md", base / ".claude" / "CLAUDE.md"]
        notes += sorted((base / ".claude" / "rules").glob("*.md"))
    notes = list(dict.fromkeys(notes))
    hooks = sorted((CLAUDE / "hooks").glob("*"))
    for t in terms:
        found[t]["notes"] = []
        for n in notes + hooks:
            try:
                lines = n.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            hits = [(i, l) for i, l in enumerate(lines, 1) if rx[t].search(l)]
            if not hits:
                continue
            if n in hooks:
                found[t]["notes"].append(f"{n} (hook script, {len(hits)} lines mention it)")
            else:
                found[t]["notes"] += [f"{n}:{i}: {mask(l.strip())[:220]}" for i, l in hits]
    return found


def report(found, limit):
    caps = {"user": limit * 3, "prompt": limit, "setup": limit * 2, "reported": limit}
    for t, r in found.items():
        dates = sorted(x[0] for k in caps for x in r[k])
        span = f"{dates[0]} to {dates[-1]}" if dates else "no mentions (proves nothing: old transcripts are deleted, other machines are missing)"
        print(f"=== {t}: {len(r['sessions'])} sessions, {span}")
        for label, key in (("USER", "user"), ("PROMPT", "prompt"), ("SETUP", "setup"), ("REPORTED", "reported")):
            items = sorted(r[key])
            if key == "reported":  # the fullest reports, in date order
                items = sorted(sorted(items, key=lambda x: -len(x[3]))[:caps[key]])
            if key == "user":  # newest first: the latest decision wins
                items = items[::-1]
            for when, proj, sess, text in items[:caps[key]]:
                print(f"  {label:<8} {when} {proj} [{sess}] {text}")
            hidden = len(r[key]) - min(len(items), caps[key])
            if hidden > 0:
                print(f"  {label:<8} … {hidden} more (raise --limit)")
        for n in r["notes"]:
            print(f"  NOTE     {n}")
        print()


def self_test():
    global TERMS
    TERMS = ["webcrawler"]
    cases = {
        "Authorization: Bearer abc123SECRETxyz": "Authorization: Bearer [masked]",
        "token=hunter2abc": "token=[masked]",
        '"api_key": "sk-proj-abcDEF123ghi456"': '"api_key": [masked]',
        "export X=ghp_abcdefABCDEF1234567890": "export X=[masked]",
        "run webcrawler via podman": "run webcrawler via podman",
        "id 3f9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c": "id [masked]",
        "call mcp__webcrawler__screenshot now": "call mcp__webcrawler__screenshot now",
        "tool --password hunter2abc --x": "tool --password [masked] --x",
        "curl -u admin:s3cret http://x": "curl -u admin:[masked] http://x",
        "https://user:pa55word@host/x": "https://user:[masked]@host/x",
    }
    for raw, want in cases.items():
        got = mask(raw)
        assert got == want, f"mask({raw!r}) = {got!r}, wanted {want!r}"
    rx = term_regex("webcrawler")
    long_text = "x " * 200 + "password=hunter2abc and webcrawler " + "y " * 200
    assert "hunter2" not in snippet(long_text, rx), "a cut exposed part of a secret"
    TERMS = ["github"]
    assert "[masked]" in mask("export T=github_pat_11ABCDEFG0123456789_abcdefghij"), "a searched name unmasked a prefixed token"
    for raw in ("aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", "SECRET_KEY=django-insecure-x9k2zz",
                "DB_PASSWORD_PROD=hunter2", "Authorization: Basic dXNlcjpwYXNz"):
        assert "[masked]" in mask(raw), f"not masked: {raw}"
    for raw in ("mysql -u root -phunter2abc", "curl --user admin:s3cretpw http://x", "sshpass -p hunter2abc ssh host",
                "aws configure set aws_secret_access_key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY", '"password": "hunter2 abc"'):
        assert "hunter2" not in mask(raw) and "s3cretpw" not in mask(raw) and "wJalr" not in mask(raw), f"not masked: {raw} -> {mask(raw)}"
    assert "mkdir -p ~/.config/app" == mask("mkdir -p ~/.config/app"), "an ordinary -p flag was masked"
    TERMS = ["ai"]
    assert "[masked]" in mask("Xy3k_ai_9f8a7b6c5d4e3f2a1b0c9d8e"), "a short term inside a token unmasked it"
    TERMS = ["skill-inspector"]
    assert mask("skill_inspector_v2_report_2026") == "skill_inspector_v2_report_2026", "a searched name was masked"
    TERMS = ["webcrawler"]
    assert term_regex("skill-inspector").search("the skill inspector skill")
    assert not term_regex("rea").search("already created")
    transcript_test()
    print("self-test passed")


def transcript_test():
    """Session handling, answers, rejections and queued messages on a synthetic transcript."""
    global CLAUDE
    import tempfile
    sid = "11111111-2222-3333-4444-555555555555"
    long_q = "Remove zapper? " + "It costs tokens in every session and duplicates a native feature. " * 3
    rows = [
        {"type": "user", "entrypoint": "cli", "message": {"content": "keep zapper forever"}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "removing zapper now"},
            {"type": "tool_use", "id": "toolu_A", "name": "AskUserQuestion", "input": {}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_A",
            "content": f'Your questions have been answered: "{long_q}"="Leave it, never touch it". Continue.'}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "toolu_B",
            "content": "The user doesn't want to proceed. To tell you how to proceed, the user said:\nnever uninstall zapper"}]}},
        {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "zapper stays, I need it"}},
    ]
    saved = CLAUDE
    with tempfile.TemporaryDirectory() as tmp:
        CLAUDE = Path(tmp)
        proj = CLAUDE / "projects" / "p"
        (proj / sid / "subagents").mkdir(parents=True)
        (proj / f"{sid}.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        (proj / sid / "subagents" / "agent-1.jsonl").write_text(json.dumps(
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "SUBAGENT DRAFT: zapper should go"}]}}) + "\n")
        try:
            cur = search(["zapper"], sid[:8], 6)["zapper"]
            user = " | ".join(x[3] for x in cur["user"])
            for want in ("keep zapper forever", "answered: Leave it, never touch it", "rejected the call; said: never uninstall zapper", "zapper stays"):
                assert want in user, f"missing USER evidence: {want!r} in {user!r}"
            assert not cur["reported"], "the running session's own text came back as evidence"
            full = search(["zapper"], None, 6)["zapper"]
            assert len(full["reported"]) == 2, "past sessions' reports and subagent text should be found"
        finally:
            CLAUDE = saved


def main():
    global TERMS
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test()
    current, limit, terms = None, 6, []
    i = 0
    while i < len(args):
        flag = args[i]
        if flag in ("--current-session", "--exclude-session", "--limit"):
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                sys.exit(f"history.py: {flag} needs a value (an empty session id means the substitution did not happen)\n\n{__doc__}")
            if flag == "--limit":
                limit = int(args[i + 1])
            elif not args[i + 1].strip():
                sys.exit("history.py: the session id is empty (the substitution did not happen)")
            else:
                current = args[i + 1]
            i += 2
        elif flag.startswith("--"):
            sys.exit(f"history.py: unknown option {flag}\n\n{__doc__}")
        else:
            terms.append(flag.lower())
            i += 1
    if not terms:
        sys.exit(__doc__)
    TERMS = terms
    report(search(terms, current, limit), limit)


if __name__ == "__main__":
    main()

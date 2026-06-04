# Web-Client Theming + MOTD — Spec

Scope: `M14 — Polish & scale (buildable slice)`.  
Governed by the open question resolution in `docs/open-questions.md` §"Web client
customization scope": **v1 uses Evennia's default web client with light theming
only** — server name/branding, colour palette, and MOTD.  No bespoke client
build; no new npm/JS dependencies.

---

## 1. Deliverables

| # | Artefact | Location |
|---|---|---|
| T1 | CSS colour-override file | `mudgame/web/static/webclient/css/theme.css` |
| T2 | MOTD / connection-screen update | `mudgame/server/conf/connection_screens.py` |
| T3 | Webclient template override injecting the CSS | `mudgame/web/templates/webclient/webclient.html` |
| T4 | Settings: `SERVERNAME` already set | `mudgame/server/conf/settings.py` (no change needed) |

---

## 2. CSS colour palette (T1)

The theme uses a **dark-parchment dungeon aesthetic** consistent with old-school
fantasy MUDs.  The palette is expressed as CSS custom properties on `:root` so
any property in the Evennia default stylesheet that uses these variables picks
them up automatically.

| Variable | Value | Role |
|---|---|---|
| `--bg-color` | `#1a1410` | Main background (near-black brown) |
| `--text-color` | `#d4b483` | Body text (warm parchment) |
| `--accent-color` | `#8b1a1a` | Borders, headings, highlights (blood-red) |
| `--link-color` | `#c8a45a` | Hyperlinks (gold) |
| `--input-bg` | `#0f0c09` | Input-area background |
| `--input-text` | `#e8d5a3` | Input text |
| `--border-color` | `#4a3728` | Panel borders (dark brown) |
| `--scrollbar-color` | `#4a3728` | Scrollbar thumb |

The file MUST also set these properties on the `body` element and override the
webclient `.webclient` wrapper background and text colour.

```css
/* example excerpt — implementation must match */
:root {
    --bg-color: #1a1410;
    --text-color: #d4b483;
    --accent-color: #8b1a1a;
    --link-color: #c8a45a;
    --input-bg: #0f0c09;
    --input-text: #e8d5a3;
    --border-color: #4a3728;
    --scrollbar-color: #4a3728;
}

body {
    background-color: var(--bg-color);
    color: var(--text-color);
}
```

The file must define **all eight** variables.

---

## 3. Template override (T3)

Evennia locates game-dir templates before its own via Django's template engine.
Create `mudgame/web/templates/webclient/webclient.html` that:

1. Extends Evennia's stock webclient template:  
   `{% extends "webclient/base.html" %}`
2. Injects the CSS override using a `{% block extra_head %}` block (or
   equivalent block name in Evennia's webclient base template).

The block must emit a `<link>` tag referencing
`{% static 'webclient/css/theme.css' %}`.

---

## 4. MOTD / connection screen (T2)

Replace the boilerplate `CONNECTION_SCREEN` in
`mudgame/server/conf/connection_screens.py` with a themed MOTD that:

- Opens with the game's title: `Keep on the Borderlands`
- States the session is in Open Beta / early access
- Names the telnet and web-client access methods
- Includes the standard `connect` / `create` / `help` / `look` instructions

### Required lines (verbatim or functionally equivalent)

1. A title line containing `"Keep on the Borderlands"`.
2. A line containing `"connect <username> <password>"`.
3. A line containing `"create <username> <password>"`.
4. A line containing `"help"` and `"look"`.

The screen must still be formatted with Evennia colour codes (`|b`, `|g`, `|n`,
etc.) and must reference `settings.SERVERNAME`.

---

## 5. Acceptance criteria

- [ ] `mudgame/web/static/webclient/css/theme.css` exists.
- [ ] `theme.css` defines all eight CSS custom properties listed in §2.
- [ ] `mudgame/web/templates/webclient/webclient.html` exists.
- [ ] `webclient.html` extends Evennia's base template and injects the CSS link.
- [ ] `connection_screens.py` `CONNECTION_SCREEN` string contains
      `"Keep on the Borderlands"`, `"connect"`, `"create"`, `"help"`, `"look"`.
- [ ] `SERVERNAME` in `settings.py` == `"Keep on the Borderlands"` (no change
      needed; verified by test).
- [ ] `ruff`, `mypy --strict`, and `pytest tests/web_theming/` all pass.

---

## 6. Test plan (`tests/web_theming/`)

All tests are pure-Python, no Evennia boot required.

| ID | What it checks |
|---|---|
| `test_css_file_exists` | File present at expected path |
| `test_css_variables` | All eight custom properties present in file content |
| `test_template_exists` | Template file present |
| `test_template_extends` | Template contains `extends` and `extra_head` block |
| `test_template_css_link` | Template contains `theme.css` static reference |
| `test_connection_screen_title` | Screen contains `"Keep on the Borderlands"` |
| `test_connection_screen_commands` | Screen contains `connect`, `create`, `help`, `look` |
| `test_servername_setting` | `SERVERNAME == "Keep on the Borderlands"` |

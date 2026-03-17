
* `frontend/src/pages/McpSettings.tsx` only really generates a **Claude-style** block. Cursor/Windsurf are just UI buttons, and there is nothing for **OpenCode** or **Codex**.
* That page is also internally broken: it tries to use `k.key_hash`, but `backend/app/api/admin/api_keys.py` returns only `id`, `label`, `status`, and `created_at` on list. So the page cannot generate a valid auth value from the current API.
* `backend/app/api/mcp/server.py` currently exposes only **2 tools** (`chat`, `generate_image`), which is far below the “all software / all features” goal.
* `backend/app/main.py` does not mount an MCP router, so the MCP server is effectively a **separate service concern**, not something the main admin API can silently assume is healthy.

Also, for true cross-client support, your MCP transport strategy needs to change. Claude Code now recommends **HTTP remote MCP** and marks SSE as deprecated, Codex supports **STDIO and streamable HTTP** with bearer token auth, and OpenCode supports **remote MCP** configured with `url` and `headers`. So your “universal” path should be **HTTP first**, with optional SSE/STDIO compatibility modes. ([Claude API Docs][1])

## 1) MCP configuration page: implementation plan

Create a new page called something like **Integrations → MCP Clients**.

### A. What this page should do

* Show **MCP server status** separately from API status:

  * API reachable
  * MCP reachable
  * auth required / not required
  * tools discovered count
  * last verified time
* Show **client-specific tabs**:

  * Claude
  * Codex
  * OpenCode
* For each tab, show:

  * what file/path to edit
  * copy-paste config
  * CLI add command if supported
  * verify command
  * common troubleshooting

This matters because these clients do not use the same config shape:

* Claude uses `claude mcp add`, JSON config, and `/mcp` / `claude mcp list`. SSE is deprecated in Claude Code docs. ([Claude API Docs][1])
* Codex stores MCP config in `~/.codex/config.toml`; CLI/app/IDE share that config; it supports STDIO and streamable HTTP with bearer token auth. ([OpenAI Developers][2])
* OpenCode uses `~/.config/opencode/opencode.json`, supports remote MCP under `mcp`, and lets you pass headers. It also has `opencode mcp list`. ([OpenCode][3])

### B. Token/auth redesign

Do **not** build this page around “select existing API key from list”.

Instead:

* add **Create MCP token**
* reveal raw token **once**
* allow copy immediately
* show masked token afterward
* allow revoke/regenerate

Reason: with your current backend design, raw keys are not recoverable later, so a list-based selector is the wrong UX.

### C. Transport strategy

Make this order of support:

1. **Remote HTTP MCP** as primary
2. **STDIO helper mode** as optional
3. **SSE legacy mode** only if you must keep backward compatibility

### D. Client-specific outputs

The page should generate these blocks:

* **Claude**

  * `claude mcp add --transport http ...`
  * JSON config block
  * verify with `claude mcp list` and `/mcp` ([Claude API Docs][1])

* **Codex**

  * `config.toml` block under `[mcp_servers.<name>]`
  * optional CLI workflow note
  * verify in TUI with `/mcp` and CLI help/manage flow ([OpenAI Developers][2])

* **OpenCode**

  * `~/.config/opencode/opencode.json`
  * remote `mcp` entry with `type`, `url`, `headers`
  * verify with `opencode mcp list` ([OpenCode][4])

### E. Verification flow on the page

Add a built-in checklist:

* endpoint reachable
* auth header accepted
* tools listed successfully
* sample tool call dry-run
* client config syntax valid
* copy-paste preview exactly matches selected host/token

### F. Todos

* fix current broken token flow
* split MCP health from API health
* add HTTP remote MCP endpoint as primary
* expand tool registry beyond 2 demo tools
* add client tabs for Claude, Codex, OpenCode
* add OS/file-path help per client
* add “copy config” + “copy command”
* add live verification badges
* add troubleshooting cards

---

## 2) OpenClaw package + plugin + skill: implementation plan

I also reviewed the OpenClaw docs. Best path: ship a **native OpenClaw plugin package** first, with bundled **skills** inside it. OpenClaw supports native plugins via `openclaw.plugin.json`, and package-based plugins can declare `openclaw.extensions` in `package.json`. It also supports installing from a local directory, `.tgz`, or `.zip`, which matches your “not in npm repo yet” requirement. ([OpenClaw][5])

### A. Deliverables

Build 3 deliverables:

1. **OpenClaw plugin package**

   * native plugin
   * versioned
   * installable from `.tgz` and `.zip`

2. **Skill pack inside the plugin**

   * one or more `skills/` directories
   * each skill contains `SKILL.md`
   * skill teaches OpenClaw how to use your gateway/tools well ([OpenClaw][6])

3. **Dedicated admin page**

   * download latest package
   * install instructions
   * verify instructions
   * changelog / version / checksum
   * troubleshooting

### B. Plugin packaging strategy

Use:

* `openclaw.plugin.json` for native plugin metadata/config
* `package.json` with `openclaw.extensions`
* optional `skills` entries via manifest
* optional `setupEntry` later if onboarding/config UI becomes important ([OpenClaw][5])

### C. Manual install flows to support on the page

Because it is not in npm initially, the page should show:

* install from local folder
* install from `.tgz`
* install from `.zip`
* dev link mode for local development

OpenClaw documents all of these install paths, plus `plugins list`, `plugins info`, `plugins doctor`, enable/disable, and update flows. ([OpenClaw][7])

### D. Skill strategy

Create at least 2 skills:

* **gateway-operator**

  * explains how to use your gateway tools safely and when
* **gateway-troubleshooter**

  * helps diagnose auth, transport, tool discovery, and connectivity issues

OpenClaw skills are just folders with `SKILL.md`, and they can be inspected with `openclaw skills list`, `info`, and `check`. OpenClaw also suggests testing with `openclaw agent --message "use my new skill"`. ([OpenClaw][6])

### E. Dedicated page for OpenClaw

Create **Integrations → OpenClaw** with:

* latest version
* compatible OpenClaw versions
* download `.tgz`
* download `.zip`
* install commands
* enable/disable steps
* verify steps
* expected tool list
* expected skill list
* known issues
* checksums
* release notes

### F. Test plan

I did **not** perform a live OpenClaw install in this environment, so this part should be treated as the acceptance checklist, not a completed runtime validation.

Test matrix:

* install from `.tgz`
* install from `.zip`
* install from linked local directory
* `openclaw plugins list`
* `openclaw plugins info <id>`
* `openclaw plugins doctor`
* `openclaw skills list`
* `openclaw skills check`
* agent can see skill
* plugin tools callable
* uninstall / reinstall cleanly
* update path works

---

## 3) Recommended rollout order

1. Fix MCP backend/auth architecture first
2. Replace current `/mcp` page with proper **Claude / Codex / OpenCode** generator
3. Add live MCP verification on that page
4. Build native OpenClaw plugin package
5. Bundle skills inside plugin
6. Add dedicated **OpenClaw** download/install page
7. Run release acceptance checklist on all install modes


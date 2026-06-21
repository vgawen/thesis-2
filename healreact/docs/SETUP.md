# HealReact — Setup Guide

Three pieces of infrastructure to wire up before Stage 2 can run.

---

## 1. Node + Playwright (zero secrets, free)

```bash
cd healreact
npm install
npx playwright install chromium
```

Verify:

```bash
npx playwright --version
npm run typecheck
```

Then fetch the benchmark apps:

```bash
npm run bench:fetch       # clones react-shopping-cart, react-admin, excalidraw
```

For each app, follow its own README to `npm install && npm run start` and
expose the dev server, then set `HEALREACT_BASE_URL=http://localhost:PORT`
before running tests.

---

## 2. LLM API key — what it actually pays for

There are **two independent uses** of LLMs in this project. Don't conflate them.

| # | User | Why | Required auth | Cost estimate |
|---|------|-----|--------------|----------------|
| A | **HealReact itself (the method)** — write-time intent labelling, runtime selector repair, oracle explanation | This is part of the system under test; the paper measures its cost (Claim C4) | `OPENAI_API_KEY` env var (default, GPT-4o-mini class), **or** a local vLLM endpoint via `HEALREACT_LLM_BASE_URL` if you want zero-key but need a GPU | ≤ $0.05 / heal × ~2k heals = **≤ $100** for full benchmark |
| B | **`/auto-review-loop` (Stage 3) — Codex GPT-5.5 xhigh as independent reviewer** | Without this, Stage 1's adversarial review stays "same-model" and Stage 1 can never become `accepted` | **Already done** — `codex login` returned "Logged in using ChatGPT". Uses your ChatGPT Plus/Pro/Team plan, no separate key. | $0 marginal (counts against your plan quota) |

Total external API budget for HealReact (use A only) if you go fully cloud:
**≤ $100**, as written in `refine-logs/EXPERIMENT_PLAN.md §E5`. Use B is
free under your existing ChatGPT plan.

### How to wire the keys (no secrets in repo)

Add to your shell (`~/.zshrc`):

```bash
export OPENAI_API_KEY="sk-..."         # if you go cloud
# OR for use-A-only with a local model:
export HEALREACT_LLM_BASE_URL="http://localhost:8000/v1"
export HEALREACT_LLM_MODEL="deepseek-coder-v2-instruct"
```

The `healreact/.env.local` file is **gitignored** so you can keep
project-scoped keys there if you prefer:

```bash
# healreact/.env.local  (NEVER commit)
OPENAI_API_KEY=sk-...
HEALREACT_LLM_MODEL=gpt-4o-mini
```

---

## 3. Codex MCP server — needed for `/auto-review-loop`

The skill `/auto-review-loop` references the MCP tool `mcp__codex__codex`.
This tool is exposed by the OpenAI Codex CLI in MCP-server mode.

### Already done in this workspace

- ✅ Codex CLI installed: `@openai/codex` v0.139.0 (verified `codex --version`).
- ✅ Already authenticated: `codex login status` → "Logged in using ChatGPT".
- ✅ Project-scoped MCP config written: `.cursor/mcp.json` registers `codex` as `codex mcp-server` (stdio).

### What YOU need to do

1. **Fully restart Cursor** — `cmd+Q` then reopen. MCP tool lists are fixed
   at session start; no hot reload. After restart, the agent in the
   next session has `mcp__codex__codex` available as a tool.

2. **(Optional) make it global** — if you want Codex MCP in every Cursor
   project, merge this snippet into `~/.cursor/mcp.json` (don't replace,
   merge — your existing Figma entry must stay):

   ```json
   {
     "mcpServers": {
       "Figma": { "url": "https://mcp.figma.com/mcp", "headers": {} },
       "codex": { "command": "codex", "args": ["mcp-server"] }
     }
   }
   ```

3. **Smoke test from the new session** — ask the agent: *"Use Codex MCP
   to summarise `idea-stage/IDEA_REPORT.md` in 3 bullets."* If the tool
   call succeeds, you're done.

### Verifying without restarting Cursor

You can manually drive `codex mcp-server` over stdio to confirm it boots:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1"}}}' | codex mcp-server
```

If you get a JSON-RPC response (not a crash), Cursor will be able to talk to it after restart.

---

## 4. Stryker.js for mutation testing (Stage 2, bench construction)

Per benchmark app:

```bash
cd bench/ReactHealBench/apps/react-shopping-cart
npm install --save-dev @stryker-mutator/core @stryker-mutator/jest-runner
npx stryker init     # accept defaults; pick Jest as test runner
npx stryker run      # generates surviving / stubborn mutants
```

We only keep **surviving** mutants for the false-heal probe (E3 sweep).

---

## What I (the agent) did NOT do for you

- I did **not** set any environment variable on your machine — that requires you to edit your shell rc.
- I did **not** start any long-lived service (vLLM server, dev server, MCP server) — restart Cursor after Codex install, and start the per-app dev servers manually.
- I did **not** commit any secret. `.env.local` is gitignored.

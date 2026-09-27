# DECISIONS.md — Computer-Use Automation System (interface.ai take-home, Assignment A)

Working log of every design decision for **our implementation**. Each entry has the same shape:

- **Question** — what we had to decide
- **Options** — what we considered
- **Chosen** — what we picked
- **Reasoning** — why, argued against the assignment
- **Brief ref** — which section of the assignment it serves

This file is the raw material for `REPORT.md` (7 required headings) and `README.md`. It is not the report itself.

---

## 0. What the assignment requires (the yardstick)

**Through-line:** *The model discovers. The artifact becomes a reusable capability. Deterministic replay is how an AI agent invokes it in production.*

**Must-have (Section 3):**

| Ref | Requirement |
|---|---|
| 3.1 | Goal-driven LLM loop (observe → decide → act) on a real UI; stops on goal, max steps, timeout, or dead end. Bias toward approaches that work with no clean DOM. |
| 3.2 | Typed, versioned, reviewable artifact: ordered steps, how each element is identified (with robustness reasoning), typed inputs, typed outputs, checkpoint/success condition. "Focal point of the evaluation." |
| 3.3 | Deterministic replay, **no LLM in the decision loop**: stable targeting, checkpoint verification, declared outputs returned. Must separate **business outcome / recoverable condition / hard failure**. Structured result with step, expected, observed. |
| 3.4 | Safety: explicit configurable allowlist (domains/routes, action types); safe vs. risky actions handled conservatively; never persist secrets or raw sensitive data. |
| 3.5 | Evidence: structured log of what and why, plus at least one richer failure signal. |
| 3.6 | Human-in-the-loop: detect stuck, raise request with context, human takes control of the **same live session**, hands back, human actions recorded. Mock operator UI is allowed; the mechanism must be real. |
| 3.7 | Design (not build) for heterogeneous surfaces and multi-tenant reuse, incl. drift. Core abstractions must not "paint you into a corner". |

**Fixed rules (Section 4):** at least one *real* LLM-driven discovery run with evidence in `/evidence/`. Everything else is our call, but must be defended.

**Scope (Section 5):** a thin-but-real vertical slice touching *every* Section 3 requirement, not a polished subset. Depth goes into the artifact schema, replay + error handling, and the safety/escalation model. Do not build scaling infrastructure. Say what we cut.

**Deliverables (Section 6):** public repo with `README.md` (setup + demo path); `REPORT.md` with 7 exact headings (Architecture, Artifact schema, Determinism & error handling, Heterogeneity & multi-tenant, Escalation & handoff, Safety, Cuts); `/evidence/` with a saved artifact and logs from a discovery run **and** a replay run, ideally including one replay that hits an error.

**Graded roughly in this order (Section 7):** system design → core loop correctness → robustness/error handling → human-in-the-loop → generalization → safety/data handling → code quality → communication.

---

## 1. Requirement → decision map

| Requirement | Decisions |
|---|---|
| 3.1 Agent loop | D1, D2, D3, D4, D5, D6, D19 |
| 3.2 Artifact | D7, D8, D9, D12, D21, D23, D29 |
| 3.3 Replay & errors | D9, D10, D12, D26, D27, D28 |
| 3.4 Safety | D11, D15, D16, D17, D18, D20, D32 |
| 3.5 Evidence | D24, D30 |
| 3.6 Escalation | D14, D19, D20, D28 |
| 3.7 Heterogeneity / multi-tenant | D2, D8, D21, D22, D32 |
| Section 6 / code quality | D25, D31 |

---

## A. Foundations

### D1 — Target application

**Question:** Which application do we automate as a stand-in for a bank back-office system?

**Options:**
- (a) **ParaBank** — public banking sandbox built for automation practice.
- (b) A local mock bank app we build, hostile DOM (framesets, nested tables, no test IDs), with switches to inject failures.
- (c) Both.

**Chosen:** (a) ParaBank.

**Reasoning:**
- Zero build time on the app; all effort goes to the graded parts (schema, replay, safety, escalation), per Section 5.
- Banking-flavoured, matching the real use case, and has a natural multi-step flow (login → accounts → detail) and a natural risky action (Transfer Funds).
- Real business outcomes exist for free (nonexistent account).
- Brief explicitly permits "a public demo/sandbox site" and asks that we respect terms and rate limits and never use real credentials or PII.
- **Known cost:** the DOM is clean, so the legacy/no-clean-DOM story cannot be *shown* in code; it is argued in the report through the `Surface` seam (D22) and the ranked locators (D8). Also, being a third-party server, we cannot force failures on demand; we inject faults browser-side instead (D30).

**Brief ref:** Section 4 (target application), 3.7, Section 9 (ground rules).

---

### D2 — How the agent perceives and acts on the UI

**Question:** During discovery, how does the LLM see the page and choose what to do?

**Options:**
- (a) Accessibility tree / DOM text only.
- (b) Screenshot + pixel coordinates.
- (c) Hybrid: screenshot **and** a numbered element list; the model picks an element number; the code resolves the number to a real element.

**Chosen:** (c) Hybrid.

**Reasoning:**
- 3.1 says to *bias toward an approach that would still work with no clean DOM* — the common case at banks. Text-only (a) fails when markup has no roles or names (e.g. an image-button in a table cell). The screenshot gives the model real visual grounding there.
- Pure coordinates (b) are the only option for a native desktop app, but coordinates break on resolution or layout change and directly conflict with "replay works next month".
- In (c) the model only *points* at element `[3]`. The action and the recorded locator resolve to the real element. **Pixels are never persisted.** The number is temporary; the saved artifact stores a description of the element (D8).
- This is the concrete answer to the surface-abstraction question in 3.7: perception can change (DOM, accessibility API, vision) without changing the artifact.
- **Cost:** more moving parts (screenshot capture, numbering, image tokens every step) than a plain-DOM app strictly needs.

**Brief ref:** 3.1, 3.7.

**How the loop actually works, and what "reasoning" means here.**

```
flowchart LR
    Start(["Real browser page"]) --> Scan

    subgraph LOOK["① LOOK — one scan feeds two outputs"]
        direction LR
        Scan["Read the live DOM once<br/>(our code, not the agent)<br/>role, label, text, current value<br/>assign a NUMBER to each element"]
        Scan --> DrawShot["Draw the numbered boxes<br/>→ take screenshot<br/>→ remove the boxes"]
        Scan --> List["Write the text list<br/>from the SAME numbers<br/>e.g. '1 textbox Username'"]
    end

    DrawShot --> Reason
    List --> Reason

    subgraph THINK["② THINK — the agent, powered by the LLM"]
        direction LR
        Reason["Looks at: goal, picture + list,<br/>history so far, its own rules"]
        Reason --> Decide["Decides to CALL ONE TOOL<br/>with a number<br/>e.g. type_text, ref = 1"]
    end

    Decide --> ToolRun

    subgraph ACT["③ ACT — the agent's tool call runs"]
        direction LR
        ToolRun["Tool's OWN code runs<br/>not the LLM's judgment"]
        ToolRun --> Safety["Safety checks:<br/>deny-list, approval gate,<br/>already declined?"]
        Safety --> DoIt["Resolve the number,<br/>tell the browser<br/>to actually do it"]
    end

    DoIt --> Start
```

LOOK is one scan feeding two outputs (the picture and the list), not two separate perception channels.

**What "scan the page once" actually does.** It is not reading the raw HTML source as text, and it is not the screenshot either — those are two different things people sometimes assume it is. It reads the browser's live **DOM** (the rendered structure the browser holds in memory, not the static HTML file): a small script run *inside* the already-loaded page, asking the browser directly for its live, rendered elements — every link, button, non-hidden input, dropdown, textarea, and anything explicitly marked as a button/link role. For each one it works out: its **role** (an `<input type="submit">` and a `<button>` both resolve to `"button"`), its **name** (tried in order: an `aria-label`, then a real `<label>` pointing at it, then its own text/value, then a placeholder/title/alt/name attribute — first one found wins), its **current value** (skipped for passwords and buttons), and its **on-screen position and visibility** (anything with zero size or `display: none` is skipped entirely). Only after all of that is numbered does drawing and the screenshot happen.

**This whole scan is our own fixed code (`OBSERVE_JS`), not the agent.** The LLM is not invoked for this step at all, has no say in how a role or a name gets computed, and only ever sees the finished result — the numbered picture and the text list — once this has already run.

The number is thrown away after every step; nothing about "box [1]" or its pixel position is ever saved. Only a *description* of the element (D8) gets saved, for replay later.

"Reasoning" is not multi-step planning done once — at every single moment the agent looks fresh at the same four things (goal, current picture+list, history so far, its own rules) and decides to call one tool. That step repeats for the whole run.

A distinction worth keeping explicit: **the agent decides *which* tool to call; the tool's own code decides *whether it is allowed to happen*.** The LLM can ask for anything — the deny-list, the approval gate (D33), and the locator resolution all run inside the tool's own code, unconditionally, whatever the LLM intended. This is why the system's safety does not depend on the model's judgment.

**Worked example.** Goal: *"Log in and read the balance of account 14232."*

| # | What the agent SEES | What the agent THINKS | Tool the agent calls (then the tool's own code executes it) |
|---|---|---|---|
| 1 | Login page. List: `[1] textbox "Username"`, `[2] textbox "Password"`, `[3] button "Log In"` | "This is a login form. My rule says: log in first, using the stored secret, never type a real password myself." | `type_secret(ref=1, name="username")` |
| 2 | Same page, box [1] now shows filled dots | "Username's in. Password box is still empty." | `type_secret(ref=2, name="password")` |
| 3 | Both boxes filled | "Both fields are filled. Time to submit." | `click(ref=3)` |
| 4 | New page: Accounts Overview. List: `[1] link "13899"`, `[2] link "14232"`, `[3] link "Transfer Funds"` | "The page changed, so I'm logged in. My goal needs account 14232, and I see it right there as [2]." | `click(ref=2)` |
| 5 | New page shows "Balance: $1,200.00" in the text | "The value I need is right here on the page. Nothing left to click." | `page_text()` |
| 6 | Text back: "...Balance: $1,200.00..." | "Found what I needed. Goal's done." | `finish(values={"balance": "$1,200.00"})` |

Every row is one full look→think→act moment. The model never sees raw code or pixel coordinates, only numbered pictures — and what gets written down afterward (for replay, D8) is never the number, only what the number *meant*, so it still works next time the page loads with different numbering.

---

### D3 — Language and runtime

**Question:** What do we build in?

**Options:** (a) Python + Pydantic. (b) TypeScript + Zod.

**Chosen:** (a) Python.

**Reasoning:**
- The artifact schema is the focal point of grading. Pydantic gives strict typing, validation, and versioning of a schema for very little code, and serialises cleanly to YAML.
- Mature Playwright, Anthropic SDK, and deep agents bindings in one language.
- TypeScript is equally viable (Playwright is native there); it just adds ceremony for the schema/versioning story.

**Brief ref:** Section 4 (language), 3.2, code quality.

---

### D4 — Agent framework for discovery

> **Update (Phase 1):** GO confirmed. Deep agents work with our own Playwright tools. Their pause rule (`interrupt_on`) is no longer used for safety; see D33 and section K.

**Question:** What runs the observe → decide → act loop?

**Options:**
- (a) Plain Python loop calling the Claude API.
- (b) Custom LangGraph graph (nodes: plan, observe, decide, act, check-stuck, escalate).
- (c) **Deep agents** (`create_deep_agent`) with our own browser tools.

**Chosen:** (c) Deep agents, for **discovery only**. Revisit if it fights with Playwright.

**Reasoning (from reading the deepagents docs):**
- Built in: a `write_todos` planning tool (useful for multi-part goals), automatic context summarisation (long runs), checkpointed/durable execution, and human-in-the-loop via `interrupt_on`.
- `interrupt_on` pauses **before** a tool executes, supports `approve` / `edit` / `reject`, and accepts a `when` predicate so only specific calls pause (e.g. only the final Transfer click). This maps directly onto our risk rule (D20).
- It **requires a checkpointer** and resume with the same `thread_id` via `Command(resume=...)`.
- **Two limits we must design around:**
  1. `interrupt_on` is an approval gate on a tool call, **not** a live-session handoff. Letting a human drive the browser is our own code (D14).
  2. The checkpoint saves the *agent's* state, **not the browser**. The browser must live outside the agent in our process, so the process stays alive during a handoff (D25, D28).
- Sub-agents and the virtual filesystem go unused; we accept that unused surface area for the planning, summarisation, and approval features.
- Loops are not solved by any framework; we solve them with our own stuck rules (D19).
- Replay is **not** an agent (D6), so deep agents apply only to discovery.
- **Fallback:** if deep agents fight our Playwright tools, drop to a custom LangGraph graph (b) with the same tools and rules; only the loop shell changes.

**Brief ref:** 3.1, 3.6, Section 4 (LLM loop structure).

---

### D5 — Where the browser tools come from

**Question:** Playwright MCP server, or plain Playwright with our own tools?

**Options:** (a) Playwright MCP server. (b) Plain Playwright library + our own tools (`click`, `type`, `extract`, `screenshot`, `ask_human`).

**Chosen:** (b).

**Reasoning:**
1. **Recording (3.2):** the artifact must store how to *find* each element. With our own tools every click records its locator at the moment it happens. With MCP we would reconstruct locators afterwards from another process's output.
2. **Live handoff (3.6):** a human must take over the *same* browser we hold. With MCP the browser lives in the server's process.
3. **Numbered screenshot (D2):** MCP does not provide it; we would write it either way.
4. **Enforcement (3.4):** allowlist and risk checks sit in our tool code, before Playwright runs. Tools we do not own cannot be checked before they act.
5. Single process is easier to explain and defend.

**Brief ref:** 3.1, 3.2, 3.4, 3.6.

---

### D6 — Replay is not an agent

**Question:** Who or what executes the artifact in production?

**Chosen (clarification, not a branch):** Exactly one agent exists: the discovery agent. Replay is a fixed, generic **replay engine** we write once in plain code. Stack:

```
Artifact (YAML data) → Replay engine (our loop, checks, errors) → Playwright → Browser → ParaBank
```

**Reasoning:**
- 3.3 says replay must run "without invoking the LLM for decisions". The engine only follows saved steps and checks results.
- The company's own AI agent (the caller that decides "get this member's balance") is out of scope; our only contact with it is the artifact's contract (inputs, outputs, result statuses).
- Only permitted exception is the optional "assisted fallback" stretch goal; not planned.

**Brief ref:** 3.3, Section 1 (the "hands" framing).

---

### D7 — Artifact file format

**Question:** How is the artifact stored on disk?

**Options:** (a) YAML. (b) JSON.

**Chosen:** (a) YAML, always validated through a Pydantic model.

**Reasoning:**
- 3.2: a *human reviewer* and a calling agent must both understand it. YAML reads closer to plain English and allows comments (e.g. why a locator was chosen).
- Pydantic keeps it strictly typed; format is just how it looks on disk. JSON would work equally well for machines.

**Brief ref:** 3.2, Section 4 (how it is stored/serialised).

---

### D8 — How each element is identified (locator strategy)

**Question:** How does the artifact describe "the element to act on" so replay finds it without the LLM, next month?

**Options:**
- (a) One locator per element.
- (b) A **ranked list** of locators tried in order, each with a stability note.
- (c) (b) plus a saved image crop as a last-resort visual fallback.

**Chosen:** (b).

**Reasoning:**
- Ranked list: (1) role + accessible name, e.g. *button "Log In"* — most stable, and the same identity across differently branded tenants; (2) visible text / label; (3) structural position scoped to a container (e.g. *3rd input inside the login form*) — weakest, but better than a hard failure.
- Replay logs **which level** matched. Falling to weaker levels repeatedly is our drift signal (D21).
- A single locator (a) fails the whole replay on one mismatch.
- Image crop (c) rejected: adds a matching dependency, is brittle to resolution, and image crops can capture sensitive values (cuts against D16). Kept as a described idea for desktop surfaces in the report.
- Never use a global index over all clickable elements (`nth=18` of the whole page): it breaks whenever any link is added.

**Brief ref:** 3.2 ("how each target element is identified, with reasoning about robustness"), 3.3 (stable targeting).

---

### D9 — Checkpoint / success condition

**Question:** How does replay confirm it reached the expected state rather than assuming the click worked?

**Options:** (a) URL check only. (b) Page-content check only. (c) Both must match.

**Chosen:** (c).

**Reasoning:**
- Some pages change content without changing URL; others share a URL across states. Two independent signals must agree, so a false "success" is far less likely.
- Cheap: two lines in the YAML, reusing the same page-reading tooling.

**Brief ref:** 3.2 (checkpoint/success condition), 3.3 (verify the checkpoint).

---

## B. Errors, replay behaviour, result contract

### D10 — Where error-handling rules come from

**Question:** How does replay tell "no such account" from a crash? Where do the rules live?

**Options:** (a) Declared in each artifact. (b) Built into the engine as one generic list. (c) Engine defaults **plus** per-artifact rules.

**Chosen:** (c). Three buckets:
1. **Business outcome** — a valid answer (e.g. `ACCOUNT_NOT_FOUND`). Returned as a result, not an error.
2. **Recoverable** — slow load, known popup, session expiry. Handle and continue.
3. **Hard failure** — expected element gone, all locators failed, checkpoint never met. Stop, capture evidence, surface a clear error.

**Reasoning:**
- Timeouts and session expiry are the same everywhere → engine defaults, written once.
- Business outcomes are specific to each flow → declared in the artifact as rules like *when page shows "could not find account" → `ACCOUNT_NOT_FOUND` (business)*. Checked **after every step**, not only at the end.
- Discovery finds these by running one deliberate bad-input probe so the model sees the error state once and the recorder saves the pattern. Nothing is guessed at replay time.
- The brief calls conflating business outcome with failure "the most common design mistake here".

**Brief ref:** 3.3, Section 7 (robustness), Glossary.

---

### D26 — Waiting and retries

**Question:** How does replay handle slow or flaky pages without random failures?

**Options:** (a) Fixed sleeps. (b) Wait for a condition with a timeout, bounded retries. (c) Wait for network idle.

**Chosen:** (b).

**Reasoning:**
- Before each step wait until the target is ready (visible, enabled), up to a timeout; after the action wait for the page to settle. A timeout is first a *recoverable* condition: retry up to 2 times with a short pause, then it becomes a hard failure.
- Fixed sleeps (a) are slow when the page is fast and still fail when it is slower. Network-idle (c) hangs on pages that poll in the background.
- **Never retry a data-changing step** (e.g. the final Transfer click): a repeated click could move money twice. Only reads, navigation, and safe clicks retry.
- Same inputs → same steps, so this stays deterministic.

**Brief ref:** 3.3 ("slow/failed load"), Section 7 (wait strategy).

---

### D27 — Replay result contract

**Question:** What does replay return to the caller?

**Options:** (a) Four statuses. (b) Three (fold "needs approval" into failed).

**Chosen:** (a).

| Status | Meaning | Example |
|---|---|---|
| `SUCCESS` | Done; declared outputs attached | balance returned |
| `BUSINESS_OUTCOME` | Valid answer, not a crash | `ACCOUNT_NOT_FOUND` |
| `NEEDS_APPROVAL` | Stopped before a risky step | transfer over the limit |
| `FAILED` | Hard failure with debug detail | step 4: expected button "Transfer", observed none |

Fields: `status`, `outputs`, `outcome`, `failure {step, expected, observed, evidence path}`, `run_id`.

**Reasoning:**
- 3.3 requires distinguishing success, known business outcome, and failure with *what step, what was expected, what was observed*.
- `NEEDS_APPROVAL` is not an error: the caller should wait for a human, not retry or give up. Folding it into `FAILED` would blur exactly the distinction the brief cares about.

**Brief ref:** 3.3.

---

### D28 — Continuing after a human approves

**Question:** After replay stops with `NEEDS_APPROVAL`, how does the run continue?

**Options:** (a) Hold the browser open and wait in the same session. (b) Return and end; a later call re-invokes with an approval token and starts over. (c) Build (a); describe (b) as the scaled version.

**Chosen:** (c).

**Reasoning:**
- 3.6 demands the human operate **the same live session, not a fresh one**, then hand back so the run resumes. Only (a) satisfies that.
- The result still carries `NEEDS_APPROVAL`, so a caller sees the state (D27).
- (b) is the right production shape (park the session with a timeout, reattach on approval) but is infrastructure the brief does not reward. Documented as next step.
- **Cost:** a browser is held while waiting; acceptable for a single-process CLI (D25).

**Brief ref:** 3.6.

---

## C. Safety and data handling

### D11 / D17 — Login and credentials (partly SUPERSEDED by D32)

> **Update:** the "separate login helper with hardcoded selectors" idea is replaced by agent-driven login with a `type_secret` tool (D32). What still holds: the model never sees credential values, nothing secret is saved, and `.env` holds the values.

**Question:** How does the system log in without exposing credentials?

**Options:**
- (a) Login is part of the artifact; username/password are inputs every run.
- (b) A separate login helper reads credentials from `.env`; the artifact starts on the logged-in page.
- (c) A human types the login during discovery (raised in discussion).

**Chosen:** (b), for **both** discovery and replay. Human pauses remain only for *other* sensitive fields and risky steps.

**Reasoning:**
- The helper types the password **before** the agent starts, so the model never sees it, and it never lands in the artifact, goal text, or logs (3.4).
- (c) is safe for discovery but breaks the point of replay: production replay must run unattended, and mid-run session expiry would need a person. Using one helper for both phases keeps discovery and replay starting from the same state.
- Session expiry becomes a clean recoverable case: the engine re-runs the login helper and continues.
- If the agent reaches another human-only field (e.g. an SSN), our code pauses for a human by field label; this is code, not model judgement.
- For the demo the helper reads `.env`; the report says production reads a secrets vault.
- `.env` holds `ANTHROPIC_API_KEY`, test-user credentials, optional `MODEL`; it is git-ignored, and `.env.example` documents it.

**Brief ref:** 3.4 (never persist secrets), Section 9 (keep secrets out of the repo).

---

### D32 — Agent-driven login with `type_secret` (revises D11/D17)

**Question:** A hardcoded login helper only works on ParaBank. How do we log in on *any* app without the model seeing passwords?

**Options:**
- (a) Keep a per-app login helper with hardcoded selectors (D11/D17 as first written).
- (b) The agent logs in like any other flow, using a `type_secret(ref, name)` tool. Our code types the real value from `.env`; the model only ever sees the secret's *name*.
- (c) A human types the login (rejected earlier: breaks unattended replay).

**Chosen:** (b).

**Reasoning:**
- 3.1 says the input is "a goal + a target (app/URL/entry point)"; 3.7 says abstractions must not "paint you into a corner". A ParaBank-only helper does both wrong; the agent's generic tools already work on any site, so login should too.
- The agent finds the fields itself from the screenshot and list, so it works on any login page.
- The artifact stores `{{secret:password}}` (a name), never a value. Login becomes its own recorded, replayable capability (per app, overridable per tenant, D21), also reused on session expiry.
- All ParaBank-specific values live in config (`BASE`, `ALLOWED_HOSTS`, `SECRETS` name → env var), not in agent code.
- **Guards:** `type_secret` refuses (1) unknown secret names, (2) any host not on the allowlist, (3) non-input targets; its output never contains the value. A username may appear in screenshots; D18 covering handles it.
- **Cost:** the model sees the login page and chooses fields, so login adds a few steps to discovery and can go wrong. Accepted; the verify-by-replay step (D23) catches a bad login recording.
- Ground-truth helpers that read ParaBank pages for grading stay ParaBank-only and are labelled as test scaffolding, not product code.

**Brief ref:** 3.1, 3.4, 3.7.

---

### D15 — Allowlist scope and enforcement

**Question:** What does the allowlist cover and where is it enforced?

**Options:** (a) Domains only. (b) Domains + action types. (c) Domains + action types + routes.

**Chosen:** (c), in `allowlist.yaml`, enforced **in tool code before Playwright acts**, and re-checked in replay.

**Reasoning:**
- 3.4 asks for permitted domains/routes *and* action types. Routes are cheap once domains exist and are what a bank wants ("this capability may only touch these screens").
- Enforcement in code, not the prompt: the model cannot talk its way past it.
- Replay checks it too, so a tampered artifact still cannot leave the list.
- Each artifact declares the routes it needs, so a reviewer sees its footprint at a glance.
- Off-list navigation is a hard failure, never silently ignored.

**Brief ref:** 3.4.

---

### D16 — Redaction of sensitive data in text

**Question:** How do we keep secrets and PII out of logs and artifacts?

**Options:** (a) By field label only. (b) By label **and** value pattern. (c) Log only an explicit safe list.

**Chosen:** (b), through **one** `redact()` function that every log line and artifact write must pass through.

**Reasoning:**
- Label rules catch `Password`, `SSN`; pattern rules catch look-alikes in innocently named fields (SSN-shaped, card-shaped, long account numbers → last 4 digits only).
- (c) is strictest but makes logs too sparse to debug.
- A single choke point is easy to test and defend; no scattered per-file handling for something to slip through.
- Extracted outputs (e.g. balances) are also redacted in logs; the caller still receives the real value in the result.

**Brief ref:** 3.4 ("never persist secrets or raw sensitive data"), Section 7.

---

### D18 — Screenshots

**Question:** Screenshots can show balances, names, account numbers. What do we do?

**Options:** (a) No redaction (fake data). (b) Cover sensitive fields **before** capture. (c) Cover for saved evidence only; the model sees raw.

**Chosen:** (b).

**Reasoning:**
- A small page script draws boxes over fields matching the D16 rules *before* the screenshot is taken, so both the model and the saved evidence get the covered version. One mechanism, same rules.
- ParaBank data is fake, so (a) would be harmless here but wrong for regulated data and would need an apology in the report.
- **Risk:** the model cannot read a covered field it might need. We cover only sensitive fields, not whole pages, and values the agent needs to *extract* are read through the element list, not the picture.

**Brief ref:** 3.4, 3.5.

---

### D20 — Risky vs. safe actions, and the transfer threshold

> **Update (Phase 1):** The name-based rule let a bill payment through unapproved. Now deny by default: every button except a safe list needs a human, enforced inside the click tool. See D33.

**Question:** What counts as risky, and how do we handle it?

**Options:** (a) Threshold rule: transfers up to $500 auto-run, above needs a human; per-run total also capped at $500. (b) Always require a human for any transfer.

**Chosen:** (a), limits in config.

**Reasoning:**
- **Safe / reversible:** login, navigate, search, view balances and history. **Risky / irreversible:** transfer funds, open account, pay bill, change profile.
- The brief asks us to handle the risky class conservatively and to *justify* the choice. Blanket "always ask" (b) is safest but interrupts humans for trivial actions. A threshold mirrors real bank approval limits and shows actual policy logic.
- The **amount is an input**, so the check runs on the caller's real value before the final click, in replay as well as discovery.
- The **per-run total** stops splitting a large transfer into many small ones.
- In discovery this is a deep-agents `interrupt_on` with a `when` predicate (D4). In replay, above the limit the engine stops **before the click** and returns `NEEDS_APPROVAL` with a screenshot (D27, D28).
- ParaBank has no separate confirm page, so the point of no return is the final Transfer click; we stop before it.

**Brief ref:** 3.4, 3.6 ("a risky/irreversible step needs a person to decide").

---

## D. Human-in-the-loop

### D14 — Handoff mechanism

> **Update (Phase 1):** `page.pause()` opens the Playwright Inspector (a developer tool). Replaced by our own red bar with a "Done, hand back to agent" button in the page. Same model: pause, human acts in the same live session, hand back. See section K.

**Question:** How does a human take control of the live browser, and how is control handed back?

**Options:** (a) Playwright's `page.pause()`. (b) Own pause with a terminal prompt. (c) Remote operator page over a debug port.

**Chosen:** (a), **wrapped** with our own control model.

**Reasoning:**
- `page.pause()` opens the Inspector on the *same* live page; the human acts, then presses Resume. The window handoff is already solved and tested, so effort goes to what the brief grades.
- On its own it does not say who is in control and does not record what the human did. We add:
  - a **control state** (`AUTOMATION` / `HUMAN` / `RESUMING`);
  - an **intervention request** (capability/goal, current step, covered screenshot, reason for stopping);
  - **human-action capture** through page event listeners (clicks, typing, navigation), stored in the log with sensitive values redacted;
  - evidence and context preserved across the handoff.
- (c) is closest to a real operator console, which the brief explicitly places out of scope. It goes in the report as the next step.
- The operator surface is the Inspector window: a deliberate, documented mock.

**Brief ref:** 3.6, scope note.

---

### D19 — Detecting "stuck"

**Question:** When does the system stop and call a human?

**Options:** (a) All six triggers. (b) Only step limit, repetition, and self-report. (c) Something else.

**Chosen:** (a). Any one triggers an intervention request:
1. **Step limit** (default 25 steps without reaching the goal).
2. **Same screen + same action** repeated (3 times).
3. **Repeated failures** (3 failed actions in a row).
4. **Blocked by policy** (allowlist refuses more than once).
5. **Agent asks** by calling `ask_human`.
6. **Time limit** with no progress.

**Reasoning:**
- 1–4 and 6 are our code watching the model, so we do not depend on the model noticing it is lost (the infinite-loop failure mode). 5 covers the model's own judgement.
- Each rule is a few lines; together they yield a clear "exactly when we stop" table for the report.
- The same triggers apply to replay where they make sense (unrecoverable condition, policy block), feeding the same pause path (Section 3.6 names both phases).
- Values are defaults; they live in config.

**Brief ref:** 3.1 (stopping conditions), 3.6.

---

## E. Artifact content and recording

### D12 — Extracting outputs

**Question:** How does replay read an answer (e.g. a balance) off the page?

**Options:** (a) Locator + typed format. (b) Ask the LLM to read it.

**Chosen:** (a).

**Reasoning:**
- An `extract` step uses a locator (e.g. "cell next to label *Balance*") and a declared type (`string`, `number`, `currency`).
- Validated at replay: a value that does not match its type is a hard failure, not a silent wrong answer.
- (b) would put the LLM back in replay and break 3.3.

**Brief ref:** 3.2 (typed outputs), 3.3.

---

### D29 — Getting inputs into the artifact

**Question:** The model types the real value `14898`; the recipe must say `{{account_id}}`. Who decides?

**Options:** (a) Inputs declared up front; recorder substitutes. (b) Model infers after the run. (c) (a) plus a check before saving.

**Chosen:** (c).

**Reasoning:**
- Declared, typed inputs (e.g. `account_id: string`, `amount: number`) are the calling agent's contract, so we set them rather than let the model guess.
- Before saving, scan for leftover literals that look like input data; if any remain, refuse to save and explain. This catches the classic mistake of a hardcoded value that makes replay work for one account only.

**Brief ref:** 3.2 (typed inputs).

---

### D23 — Turning a messy run into a clean recipe

**Question:** The model wanders (wrong clicks, backtracking). How do we produce the artifact?

**Options:** (a) Save every action. (b) Save only actions that worked and mattered. (c) (b), then **verify by an immediate no-LLM replay**; mark `verified` only if it passes.

**Chosen:** (c).

**Reasoning:**
- Saving everything (a) bakes dead ends into the recipe.
- The verification replay proves the artifact works *without* the model, not that the model got lucky once. It also joins discovery and replay into one coherent pipeline, which the brief says is the real test ("integration").
- Cost is one extra replay with no LLM. Gives a `draft → verified` state (a listed stretch goal) almost free; failing verification leaves it `draft`.

**Brief ref:** 3.2, 3.3, Section 5 (integration).

---

### D13 — Flows to build and demo

**Question:** Which capabilities do we implement?

**Options:** (a) One read-only flow. (b) Two: a safe read-only flow and a risky flow that stops at the irreversible step.

**Chosen:** (b).
1. **`get_account_balance`** — safe. Inputs: `account_id`. Output: `balance` (currency). Business outcome: `ACCOUNT_NOT_FOUND`.
2. **`transfer_funds`** — risky. Inputs: `from_account`, `to_account`, `amount`. Stops before the final Transfer click when over the limit (D20).

**Reasoning:**
- Read-only alone would leave escalation (3.6) and risky-action handling (3.4) untested on a real page.
- The brief's own example is "reach the confirmation screen", not "submit". Transfer Funds was preferred over "open account" as the clearest irreversible money movement.
- Cost: one extra discovery run and one extra artifact.

**Brief ref:** Section 2 (examples), 3.4, 3.6, Section 5 (vertical slice).

---

## F. Generalisation (design + schema fields, not built)

### D21 — Multi-tenant reuse and drift

**Question:** Hundreds of tenants run the same vendor product. How do we reuse artifacts?

**Options:** (a) One artifact per tenant. (b) One base artifact per vendor product + small per-tenant override files. (c) (b) plus drift detection.

**Chosen:** (c). **Design only**; the schema carries `base` and `overrides` fields so it is not a dead end.

**Reasoning:**
- Locators identify what a control *is* (role + name, D8), which survives different branding, so most steps are shared.
- An override patches only what differs (e.g. the button is "Sign In" for one tenant). A vendor update fixes the base once instead of re-recording hundreds.
- **Drift signal:** replay records which locator level matched (D8) and checkpoint results. A tenant that keeps falling to weaker locators or missing its checkpoint is flagged for review rather than failing silently. The signal is already in our logs at no extra cost.
- (a) does not scale: hundreds of tenants × ~20 apps.
- Building tenant plumbing is explicitly not rewarded (Section 7).

**Brief ref:** 3.7 (multi-tenant reuse, drift), Section 7.

---

### D22 — Surface abstraction (the seam)

**Question:** How do we avoid tying the whole system to Playwright?

**Options:** (a) Call Playwright directly everywhere. (b) A small `Surface` interface with Playwright as the one implementation.

**Chosen:** (b).

```
Agent ─┐
Recorder ├─▶ Surface ─▶ Playwright (web)  · later: desktop accessibility API, vision
Replay ─┘
```

Methods: `observe()` (screenshot + numbered elements), `act(action, target)`, `resolve(locator)`.

**Reasoning:**
- 3.7 asks for the seam between *how we perceive/act on a surface* and *the recorded flow*. A `Surface` class is that seam; the agent, recorder, and replay engine only talk to it.
- Legacy web: same interface, leaning on fallback locators. Desktop: a new `Surface` on OS accessibility APIs (screenshots as last resort); artifact and replay engine unchanged.
- Low effort (an interface plus the class we would write anyway); the discipline is never letting Playwright calls leak outside it.
- Bonus: a fake `Surface` lets replay-engine tests run with no browser (D31).
- **Honest limit:** only a web surface is built, so the interface is shaped by web; the report says so.

**Brief ref:** 3.7 (surface abstraction).

---

## G. Architecture, evidence, testing

### D24 — Evidence on failure

**Question:** What do we save so a run can be understood and debugged?

**Options:** (a) Screenshot only. (b) Screenshot + page snapshot. (c) (b) + Playwright trace.

**Chosen:** (b).

```
evidence/<run_id>/
  log.jsonl              # one line per step: what, why, result
  screenshots/           # on failure + at checkpoints (covered, D18)
  snapshot_step<N>.json  # on failure: the element list the engine saw (redacted)
```

**Reasoning:**
- 3.5 needs a structured log of what and why, plus at least one richer failure signal. Screenshot shows the problem; the snapshot explains it (e.g. "expected button *Transfer*; found only these").
- Playwright traces (c) store raw page data we cannot reliably redact, cutting against 3.4, and are large.
- Both discovery and replay write the same format so runs can be compared.

**Brief ref:** 3.5, Section 6 (`/evidence/`).

---

### D25 — Program shape

**Question:** Single program, or a service?

**Options:** (a) Single CLI process. (b) Small web service/API.

**Chosen:** (a).

```
cua discover "<goal>" --inputs ...
cua replay <capability> --account_id 14898
```

**Reasoning:**
- Meets every Section 3 requirement without infrastructure, which Section 7 says is not rewarded.
- A live process keeps the browser open, which the handoff (D14, D28) needs.
- An API wrapper (or the "agent-facing capability interface" stretch goal) is a next step in the report.

**Brief ref:** Section 4 (architecture), Section 7.

---

### D30 — Error cases shown in `/evidence/`

**Question:** ParaBank is live and public, so how do we show error handling?

**Chosen:** All five, some natural and some injected browser-side:

| Case | How produced | Bucket |
|---|---|---|
| Account not found | replay with a fake account id | Business outcome |
| Slow page | Playwright delays a request; replay waits and retries | Recoverable |
| Session expired | clear the login cookie mid-run; replay re-runs the login helper | Recoverable |
| Element missing | hide/block the Transfer button; replay fails with screenshot + snapshot | Hard failure |
| Transfer over limit | amount above $500 | `NEEDS_APPROVAL` |

**Reasoning:**
- The brief asks for at least one error replay; showing every bucket turns the error taxonomy from a claim into proof.
- Injections are a few lines each (route interception, cookie clearing) and do not harm the site.

**Brief ref:** Section 6 (evidence including an error replay), 3.3.

---

### D31 — Testing and running without live services

**Question:** What do we test, and how does someone run it with no key and no network?

**Options:** (a) Unit tests only; live runs shown as saved evidence. (b) Unit tests plus a live end-to-end test.

**Chosen:** (a).

Unit tests: schema rejects bad artifacts; redaction; allowlist; transfer threshold (incl. per-run total); replay engine per bucket using a fake `Surface`; recorder drops dead ends and catches hardcoded inputs.

**Reasoning:**
- "Tested where it counts" (Section 7): these are the load-bearing rules and run anywhere in seconds.
- Satisfies "how to run without live services" in the README.
- A live test against a public site would be flaky and could annoy the site (Section 9). The real runs are already saved in `/evidence/`.

**Brief ref:** Section 6 (README), Section 7 (code quality).

---

### D6b — Model

**Question:** Which model drives discovery?

**Options:** (a) Claude Sonnet 5. (b) Claude Opus 5. (c) Claude Haiku 4.5.

**Chosen:** (a) Sonnet 5, set in config (`MODEL`).

**Reasoning:**
- Needs vision (D2) and reliable tool use; Sonnet is strong at both at moderate cost, and one discovery run is cheap even with retries while debugging.
- Opus is likely overkill for a bank-style form flow; Haiku may lose the thread on ambiguous pages.
- Model is a config value, so swapping is one line.

**Brief ref:** Section 4 (LLM provider/model).

---

## K. Phase 1 changes (after building and testing the notebook)

### D33 — Approval is enforced inside the `click` tool (deny by default)

**Question:** How do we guarantee a human approves any action that changes data?

**Options:** (a) Framework pause rule (`interrupt_on` with a `when` predicate) reading an element flag. (b) Approval check inside our own `click` tool, for every button except a safe list.

**Chosen:** (b).

**Reasoning:**
- (a) failed twice in testing: a bill payment went through with no approval. The rule depended on an element flag, on the framework's predicate, and on notebook cell order, and any one of them could fail quietly.
- (b) has one choke point. `click` is the only tool that can submit anything, so nothing can bypass it, whatever the model does.
- Deny by default (every button except `log in`, `find transactions`) covers new buttons automatically. A name list can never be complete.
- The approval bar shows the real button and the values entered, so the human knows what they approve. A rejected button is remembered and never clicked again in that run.
- This is the "enforced in code before Playwright acts" rule from D15, applied to risky actions.

**Brief ref:** 3.4, 3.6.

### D34 — Values must come from the user, or a human enters them

**Question:** How do we stop the agent from inventing form values (payee, address, amount)?

**Chosen:** a typed or chosen value must appear in the user's goal. Otherwise the tool hands the live browser to a human, who enters it and clicks Done. Fields named ssn, password or social always go to a human.

**Update:** the first version asked the human right after login, on the start page, so the human had to navigate. Now the agent must open the task page first and point at the missing field with `request_value(ref)`; both `request_value` and `ask_human` refuse while the browser is on a start page.

**Reasoning:** with the goal "pay a bill" the agent made up a payee and an amount. A prompt rule did not stop it; a code check does. It is a crude substring match; Phase 3 replaces it with declared typed inputs (D29).

**Brief ref:** 3.4, 3.6.

### D35 — Tools run one at a time, and clicks wait for the page

**Chosen:** a lock around every tool, and a short wait plus load state after each click.

**Reasoning:** the model sent two tool calls at once; they raced on one page and login looped. Without a wait the agent saw a stale page after Log In.

**Brief ref:** 3.1, 3.3 (wait strategy).

### D36 — Secret hygiene

**Chosen:** credentials live only in `.env` (git-ignored). `.env.example` stays empty. `.gitignore` also blocks `.env.*`, keys, cookies and auth files. `nbstripout` removes notebook outputs at commit time, so balances and screenshots are not committed.

**Incident:** test-user credentials were written into `.env.example` and committed locally. Nothing had been pushed. History was rewritten and verified: no secret value exists in any commit.

**Brief ref:** 3.4, Section 9 ("keep secrets out of the repo").

## L. Phase 2 decisions (artifact schema)

### D37 — Strict, layered artifact schema

> **Update:** superseded by D63-D66, see section O. The strict-Pydantic, collect-every-problem
> approach described below is unchanged; the ranked-locator-list detail is not (see D63).

**Question:** What shape is the artifact so both a human reviewer and a calling agent can rely on it?

**Options:** (a) Free-form YAML with a light check. (b) Strict Pydantic models: unknown keys rejected, every cross-reference checked.

**Chosen:** (b).

**Reasoning:**
- 3.2 makes the schema "a focal point of the evaluation". A typo (`descripton`) or a reference to a missing input must fail loudly at load time, not at 3 a.m. during replay.
- The `Capability` check collects every problem at once, so a reviewer fixes a file in one pass.
- Locators are ranked, and a page-wide index is forbidden (a structure locator needs a container). That encodes the Phase 1 lesson that global indexes break when anything is added.
- Text fields accept only `{{input}}` and `{{secret:name}}`. Secrets are names, never values, and are allowed only as typed values (D32).
- The checkpoint needs both a URL signal and a content signal (D9).

**Brief ref:** 3.2, 3.3.

### D38 — Risk is in the artifact; the limit is in config

> **Update:** superseded by D63-D66, see section O, in one respect only: `app`/`base`/`overrides`
> no longer exist (D64), so "one artifact works under different limits per tenant" is now purely
> a policy-config fact, not something the artifact's own multi-tenant fields also expressed. The
> risk/`amount_input`/`risk_level` mechanism described below is otherwise unchanged.

**Chosen:** a click step is `safe` or `risky`. A risky step names which input holds the money (`amount_input`). The capability's `risk_level` must agree with its steps. The dollar limit (D20) stays in config, not in the artifact.

**Reasoning:** the artifact says *what is risky*; policy says *how much is allowed*. That way one artifact works under different limits per tenant, and a reviewer sees the point of no return in the file.

**Applies to any money step, bill payment included.** Replay of a recorded payment needs no human to navigate or fill values (the caller supplies typed inputs), and no human for amounts up to the limit. Above the limit it stops before the final click and returns `NEEDS_APPROVAL`. Recording a flow makes it repeatable; it does not make a payment safe, which is why the irreversible step is judged by policy each time. Upgrade path, described in the report and not built: also require a previously used payee before auto-approving.

**Brief ref:** 3.4, 3.6.

### D39 — Result contract and tool contract

> **Update:** superseded by D63-D66, see section O, in one respect only: `tool_contract()`'s
> `description` field is now just `cap.description` (D66 folded `when_to_use` into it). The
> result contract (`ReplayResult`, `check_result`) is unchanged.

**Chosen:** `ReplayResult` has four statuses (`SUCCESS`, `BUSINESS_OUTCOME`, `NEEDS_APPROVAL`, `FAILED`), each requiring exactly its own fields. `check_result` checks a result against the capability: outputs must match the declared outputs, and a business outcome must be one the capability declares. `tool_contract()` derives what a calling agent sees: description, input schema, outputs, business outcomes, may-need-approval.

**Reasoning:** the brief asks that a calling agent understand what a capability needs and returns, and that business outcomes are never mixed up with failures (D10, D27). Making the shape checkable stops replay from returning ambiguous results.

**Brief ref:** 3.2, 3.3.

### D40 — Multi-tenant fields stored, not applied

> **Update: REMOVED, see D64.** `app.id`, `base`, and `overrides` are cut from the schema
> entirely (section O). Multi-tenant reuse is now purely a REPORT.md design discussion, with no
> corresponding schema field. The reasoning below (why the fields once existed) is kept as the
> record of what was tried.

**Chosen:** `app.id`, `base`, and `overrides` exist in the schema and are shape-checked. Applying an override is not built.

**Reasoning:** 3.7 asks that the core abstractions not paint us into a corner. The fields cost almost nothing now and avoid a schema change later; building the override machinery is explicitly not rewarded.

**Brief ref:** 3.7.

## M. Phase 3 decisions (the recorder)

### D41 — Capture logs events; compile is pure Python

> **Update:** superseded, see section P (D70+) below. The event-log / pure-function-compile
> *design* is unchanged and carried forward as-is; what changed is the schema and tools it is
> built against (D63-D68, D50-D69), so the concrete event fields and compile code were rebuilt.

**Question:** Where does the recorder get its facts, and how do we test it without a browser?

**Options:** (a) Rebuild locators after the run from a saved page snapshot. (b) Every tool logs an **event** at call time (tool, ok/failed, page before and after, a descriptor of the element). A pure function turns events into a `Capability`.

**Chosen:** (b).

**Reasoning:**
- This is the D5 argument made real: our own tools know the element at the moment it is touched, and the temporary `data-cua-ref` number is never stored.
- The event is plain data, so the risky logic (clean-up, login split, parameters, risk, leftovers) is unit-tested with hand-made events. A stub-page run also proved that real tool calls produce events the compiler accepts.
- Events hold typed values (needed to find literals) and secret **names**. They never hold secret values, session ids or extracted values. Raw events go to `notebooks/scratch/` (git-ignored), never to `artifacts/`.

**Brief ref:** 3.2, 3.4, code quality.

### D42 — How a descriptor becomes a ranked target

> **Update:** superseded, see section P (D70+) below. `Target(locators=[...])`, a ranked list of
> up to ~3, no longer exists (D63: `primary` + one optional `fallback`). The role-name-accessible-
> only rule and the no-positional-fallback-for-data-dependent-elements rule are both kept
> unchanged in spirit; D68's duplicate-name scoping is new.

**Question:** Which locators do we build, and when do we refuse to?

**Options:** (a) Always role+name. (b) Role+name only when the name is a real accessible name; label and text next; structure last, only inside a container.

**Chosen:** (b), with two extra rules.

**Reasoning:**
- The scanner reports **where a name came from** (`aria`, `label`, `value`, `text`, or just the `name=`/`id=` attribute). An attribute name (`fromAccountId`) is not an accessible name, so no role locator is built from it. This keeps the high-stability slot honest.
- **No positional fallback for data-dependent elements.** If the name or text contains an input (the link named `{{account_id}}`), a "1st link in the table" fallback would silently click the wrong account. So no structure locator is written for it.
- Meanings Phase 4 must honour: `label` = a `<label>`, `aria-label`, or the text of the cell just before the control in the same row. `structure nth` = the nth element of that tag inside the container, counting all of that tag. A container is the nearest form (for controls) or table, with a name only if it has `aria-label`, a caption or a legend.

**Brief ref:** 3.2 (robustness reasoning), 3.3.

### D43 — What "worked and mattered" means (D23 made concrete)

> **Update:** superseded, see section P (D70+) below. The rules themselves (drop non-actions,
> failures, repeats, dead ends, a trailing safe click) are unchanged in spirit; the concrete
> `status` values a real agent.ipynb tool call can produce today are re-derived from its current
> code (D50-D69), not the old from-scratch tools this decision was originally written against.

**Chosen:** drop non-actions, failed/denied/blocked/declined calls, and an identical repeat on the same page. Drop a **dead end**: a click that changed the page and a later click that returned to it, with nothing typed, chosen or read in between. Drop **link clicks after the last meaningful step** (typing, choosing, extracting, an approved click, or any submit button). Keep a navigate for the start page, and where the URL changed without a click. **Refuse** a run that used a human handoff (a hand-typed step cannot be recorded).

**Reasoning:** each rule is a few lines and testable. A submit button counts as meaningful even without approval, so a safe `Find Transactions` at the end is not trimmed. Refusing handoffs is safer than saving a recipe with a silent gap; the fix is to declare the value in the goal (D29).

**Cost:** two identical clicks in a row on one page are treated as a repeat. A real double "Next page" would need a review. Recorded as known limit.

**Brief ref:** 3.2, Section 5.

### D44 — Parameterisation and the leftover check

> **Update:** superseded, see section P (D70+) below. Unchanged in spirit and in mechanism
> (word-boundary matching, refuse-not-warn on leftovers, constants reported); rebuilt against the
> current `Capability` shape (`find_leftovers` walks the same fields, minus `app`/`routes`, which
> no longer exist, D64-D65).

**Chosen:** inputs are declared with the goal as `name -> {value, type, description, pattern}`. A whole typed or chosen value that equals a declared value (compared as text, or as a number so `$20.00` equals `20`) becomes `{{name}}`. Literals inside paths and locator strings are replaced with word-boundary matching (`5` is not found in `$50`, `id` is not found in `account_id`). Before saving, any declared literal still present anywhere except the `inputs` docs **refuses the save**, naming the input and the place, never the value. A typed value that matches no input is kept and **reported as a constant**.

**Reasoning:** the boundary match fixes the Phase 1 `5`-in-`$50` bug. Refusing (not warning) on leftovers is the D29 promise. Constants are only reported because a fixed value (a payee, a memo) can be legitimate, but a reviewer must see it.

**Brief ref:** 3.2 (typed inputs), 3.4.

### D45 — Login split and start page

> **Update:** superseded, see section P (D70+) below. The split rule itself is unchanged; the
> resulting login `Capability` can no longer be built as `Capability(app=App(**APP), ...)` (D64
> removed `app` entirely) and is rebuilt with `base_url` only.

**Chosen:** the kept events up to and including the first click after the last `type_secret` become `login_<app>`, with `{{secret:...}}` values and the secrets declared. The task capability contains no secret step and starts with a `navigate` to the page it began on. The login capability's checkpoint is the page after the click. The task gets a `relogin` recoverable rule when a login capability exists; the login-page text is config (`SESSION_EXPIRED_TEXT`).

**Reasoning:** D32 says login is its own capability, reused on session expiry. A first `navigate` makes replay independent of where the browser happens to be.

**Brief ref:** 3.3, 3.4.

### D46 — Extraction reads by label, and the value is never recorded

> **Update:** superseded, see section P (D70+) below. `extract_value` and `read_labeled_value`
> are rebuilt as new, additive tools in the CAPTURE half (agent.ipynb has neither), and the
> compiled `Extract` step now builds `Target(primary=LabeledValueLocator(...))` (D63), not
> `Target(locators=[LabeledValueLocator(...)])`. The reasoning (one shared reader, value never
> recorded) is unchanged.

**Chosen:** `extract_value(label, save_as, value_type, description)` calls `read_labeled_value(page, label)` (the cell after the label, the input a label points at, or the next sibling). The declared type is checked at capture. The event stores the label, name and type, **not the value**. Phase 4 replay reuses `read_labeled_value`.

**Reasoning:** balances are not clickable (Phase 1 finding). One shared reader means recording and replay cannot disagree about what "the value next to Balance:" means. Keeping the value out of the event keeps sensitive data out of every saved file (D16).

**Known limit:** this only reads *labeled* values. `transfer_funds` therefore has no output (the confirmation is a heading, not a labeled value). A `text` extract is a possible later addition.

**Brief ref:** 3.2 (typed outputs), 3.3.

### D47 — Business outcome from a probe run, and `open_path`

> **Update:** superseded, see section P (D70+) below. agent.ipynb's own `finish(summary, values)`
> has neither `outcome` nor `proof_text`, and is never modified to add them (that would be
> respelling a copied tool, not importing it). The rebuild adds a **separate** new tool,
> `finish_business_outcome(outcome, proof_text)`, instead. `open_path`'s reasoning and safety
> properties (GET-only, allowlisted, value-grounded) are unchanged.

**Chosen:** `finish` takes `outcome` (UPPER_SNAKE) and `proof_text`. The tool checks the proof text really is on the page. The recorder cuts the bad input value out of the proof text and saves a `business` rule with `when.text_present`. A probe run is never compiled as a capability. To reach a page for a bad id, the agent gets `open_path(path)`: same site only, deny words as in `click`, and every query value must be given in the goal.

**Reasoning:** D10 says discovery finds these by one deliberate bad-input probe. The agent had no way to reach a page for an id that no link points to. The proof check stops the model inventing text. Engine defaults for recoverable and hard failures stay out of scope.

**Cost:** `open_path` is a new way to move that clicks do not have. It is a GET only, allowlisted, and value-grounded. If the site shows a vague error (for example "internal error"), the rule would be too broad; the notebook prints the rule so a reviewer sees it.

**Brief ref:** 3.3, 3.4.

### D48 — Value grounding now uses declared inputs; `web_search` removed here

> **Update:** superseded, see section P (D70+) below, in name only: the value-grounding check
> this decision describes now lives in agent.ipynb's own `type_text`/`select_option` (copied
> verbatim, D50-D69), not in a from-scratch recorder tool. `open_path`'s own grounding check
> (new, D47) follows the identical rule. `web_search` is still left out, same reasoning.

**Chosen:** a typed value, chosen option or path value is allowed if it equals a declared input value, or is a whole word or number in the goal (word-boundary, not substring). Otherwise the handoff to a human happens as before, and the compile refuses that run. `web_search` is left out of the recorder's agent.

**Reasoning:** this is the D34 upgrade it promised. `web_search` sends text to a third party outside the allowlist (Phase 1 finding); discovery of a capability does not need it.

**Brief ref:** 3.4.

### D49 — Risk, checkpoint, save guards

> **Update:** superseded, see section P (D70+) below. Unchanged in spirit (approval = risky
> signal, last-kept-step checkpoint, save guards); "risky" is now read from an event's own
> `approved` flag (set by comparing `needs_human(ref)`, copied verbatim from agent.ipynb, against
> the tool's own result text) rather than a bespoke recorder-only approval mechanism.

**Chosen:**
- A click a human approved becomes `risk: risky`. `amount_input` is the declared `currency`/`number` input if there is exactly one (or one named `*amount*`). `risk_level` follows (D38).
- The checkpoint is the **last kept step's** page: `url_contains` = last path segment, `text_present` = first visible `h1`, else `.title`, else `h2`, else the page title. If there is no heading the compile refuses (D9 needs both).
- Save only after `Capability.model_validate`; refuse if a real secret value appears in the YAML (the value is never printed); never overwrite a `verified` capability; drafts start with a comment line.

**Reasoning:** the approval already exists in the click tool (D33), so it is the most reliable "risky" signal. Using the last kept step (not the finish page) means wandering after the goal does not change the checkpoint.

**Brief ref:** 3.2, 3.4.

## N. Phase 1 addendum (after Phase 3 work resumed)

### D50 — Optional model routing between Haiku and Sonnet, via a third-party service

**Question:** Should the discovery agent use one model for every step, or switch between a cheaper and a stronger model per step?

**Options:**
- (a) One model for everything (Sonnet 5, per D6b). Simplest, no new dependency, no new data leaves the process except to Anthropic.
- (b) Route in our own code: a plain rule (e.g. "before a risky click, use Sonnet; otherwise Haiku") with no external call.
- (c) `langchain-typesafe`'s `ModelRouterMiddleware`: an experimental (v0.0.1a3) library that classifies the current step by sending it to a third-party service, `api.typesafe.ai`, which needs its own paid `TYPESAFE_API_KEY`, then returns which model to use.

**Chosen:** (c), user's explicit choice after the trade-off was explained.

**Reasoning:**
- The user asked for this by name and confirmed it after being told the cost: a second third party sees step content on every turn, a new paid key is required, and the library is marked experimental.
- Kept **off by default**: the router only activates if `TYPESAFE_API_KEY` is set in `.env`. With no key, the agent behaves exactly as before (D6b, Sonnet only via `MODEL`). This means the safety story for the default path is unchanged.
- Model strings are real and verified: `anthropic:claude-haiku-4-5-20251001` (fast) and `anthropic:claude-sonnet-5` (powerful), both confirmed to build via `init_chat_model` before use. An earlier draft of this code used invented model names (`openai:luna`, `openai:sol`) that do not exist; those were not used.
- **Known gap, carried to Phase 6:** whatever text TypeSafe classifies is sent outside our process, unredacted, on every step where the router is on. This must never be enabled for a run that may show real account data, and the redaction work in Phase 6 must either cover this path too or the router must stay off for any run touching real data. For the ParaBank demo (fake data only) this is acceptable; it is called out in the report as a real-world risk.
- Not evaluated: whether Haiku is actually reliable enough for "simple" browser steps. This is untested until the user runs it with a real `TYPESAFE_API_KEY`.

**Brief ref:** 3.4 (safety and data handling), Section 4 (LLM provider/model is our call, but must be defended), Section 9 (ground rules: don't add paid services without weighing them).

### D51 — Tool triage: our own middleware, no LLM, no external call (REMOVED, see D52)

> **Update:** removed at the user's direction, after D52 was added. Keeping two overlapping tool-narrowing layers (one free/deterministic, one paid/classifier-based) was more to explain and maintain than one. D52's fail-open behaviour already covers the "no key set" case cleanly (no narrowing at all), so this layer's only unique benefit — narrowing with zero cost when TypeSafe is off — was traded away for a single, simpler mechanism. The trade-off: without a `TYPESAFE_API_KEY`, there is now no tool-selection help at all, not even the free, obvious cases (e.g. offering `page_text` on the login page). Code and its offline tests deleted from `agent.ipynb`; kept here, unmodified below, as the record of what was tried and why it existed.

**Question:** TypeSafe has no "pick the right tool" feature (checked directly against its docs and source: only a model router and a risk-blocking gate exist). How do we stop the agent from being offered tools that make no sense on the current page (e.g. `ask_human` while still on the start page, or `page_text` before login)?

**Options:**
- (a) Prompt text only ("don't call X here"). Costs nothing, but the model can still try, wasting a round trip, and we already saw this happen (D34's original bug).
- (b) `AutoModeMiddleware` (TypeSafe): blocks a call after the model makes it, no tool-list narrowing, another paid external call per tool call.
- (c) Our own middleware: before each model call, remove tool names that make no sense on the current page. Plain Python, using `ModelRequest.override(tools=...)`. No LLM call, no network call.

**Chosen:** (c), `ToolTriageMiddleware`.

**Reasoning:**
- It is genuinely faster than any LLM- or classifier-based decision: the rule is a plain function (`triage_tool_names`), and it runs in-process with no round trip.
- It never removes `observe`, `click`, `type_secret`, or `finish`, so the agent can always look, act, log in, or stop. Tested exhaustively offline: for every subset of tools and every page, that set survives.
- It is defense in depth alongside the existing code guards inside `ask_human`/`request_value` (D34): the model is now less likely to even try the call that guard would refuse, which saves a wasted step.
- Verified before writing: `AgentMiddleware.awrap_model_call` is the correct hook for an agent run via `ainvoke`/`astream` (the sync `wrap_model_call` raises `NotImplementedError` in that case); `ModelRequest` is a dataclass with a real `.override()` method used to replace `tools`.
- Always on, no key, costs nothing beyond what we already pay for the model call itself.

**Brief ref:** 3.1 (the agent loop; correctness of tool use), Section 4 (agent loop structure is our call).

### D52 — TypeSafe `Choice` for tool selection (now the only tool-selection layer)

**Question:** Use TypeSafe's `Choice` primitive to classify what job the current step is, and select tools by that job.

**Options:**
- (a) Skip tool-selection help entirely.
- (b) `Choice` decides the job (`login`, `fill_form`, `read_value`, `need_human`) each step, and the tool list narrows to that job's tools.

**Chosen:** (b). After D51 was tried and removed (see D51's update), this is the only tool-selection mechanism.

**Reasoning:**
- A page URL alone cannot tell "this step needs to fill a field" from "this step needs to read a value" on the same page. `Choice`'s own guidance line, "reach for it when options map to distinct code paths," fits this exactly: four job categories, each mapping to a fixed tool set.
- **Fail-closed would be wrong here.** A classifier can be wrong or unsure. Below a confidence threshold (0.6), the middleware changes nothing (fails open) rather than trust a shaky guess and block a tool the agent actually needs.
- **Any error fails open too**, wrapped in `try/except`: a TypeSafe outage, timeout, or auth problem must never stop the agent from working; it just runs without this layer for that step.
- **Never removes the always-allowed set:** `observe`, `click`, `type_secret`, and `finish` are always kept, whatever the classified job. Verified offline, including against an already-reduced starting set (in case a future layer is added again).
- **Same data caveat as D50, now doubled:** the current page and the last tool result's text (up to 400 characters) go to `api.typesafe.ai` on every step this is on. Real values (e.g. an account number typed by the user in the goal, or in a tool result) can appear there. Off by default, same `TYPESAFE_API_KEY` gate as D50; never enable on a run that may show real account data.
- Field names (`ChoiceAnswer.choice`, `.confidence`, `.probabilities`) and the async `ainvoke` path were confirmed against the installed package before writing this, not guessed.
- Untested against the real service: only the pure job-mapping and confidence-gate logic were run (offline, from the notebook's own cells). The live classifier call has not been exercised; that needs the user's `TYPESAFE_API_KEY` and a browser run.

**Brief ref:** 3.1, 3.4 (the redaction gap carried from D50 applies here too, and is worse: two things now leave the process per step instead of one).

### D53 — Close the gap between visual grounding and human-facing messages

**Question:** D2 gives the model a screenshot precisely so it can read a label even with no clean DOM. A real run on the loan page hit an element with no name anywhere in the code, and the human-facing message said only "field 17" — the model's own visual reading never reached it. Why, and how do we fix it?

**Cause:** `request_value(ref)` took only a number. The message it builds asks our code (`surface.name_of(ref)`) for a name, never the model. `ask_human` never had this problem, since its `question` argument already carries the model's own words.

**Chosen:** add a required `hint` argument to `request_value(ref, hint)`: the model's own reading of the field's label from the screenshot. A new `_describe(ref, hint)` combines the code's name and the model's hint when both exist, uses whichever is present, and falls back to `"field N"` only if neither is available. `type_text` and `select_option` were switched to the same helper for their own "value not given" messages, since it is a strict improvement with no downside there.

**Reasoning:** this is not a new mechanism, it is wiring the one already committed to in D2 into a place that was missing it. Tested offline: DOM name only, hint only (the reported case), both, and neither (unchanged last-resort behaviour) all give the expected message.

**Brief ref:** 3.1 (bias toward approaches that work with no clean DOM), 3.6 (an intervention request must carry enough context to act on).

### D54 — Already-filled fields: tell the model, and enforce it in code

**Question:** A real run showed every field on Bill Pay already filled (screenshot evidence), yet the agent asked again for a field ('City') that visibly had a value. Why, and how do we stop it happening again regardless of the model?

**Cause:** the element list sent to the model carries a role and a name, never the field's current value. The only way the model could notice "this is already filled" was to visually re-read the screenshot correctly, every time, across many round-trips. It didn't, and nothing in our code checked either.

**Chosen:** two changes, not one, because the model's judgment alone was exactly what failed:
1. **Tell it plainly:** the scanner now reads each input/select's current value and the element list shows it, e.g. `[7] textbox "City" = '2'`. The model no longer has to infer this from pixels.
2. **Enforce it in code:** `_ask_for_value` (used by `type_text`, `select_option`, `request_value`) now reads the field's live value first. If it is already non-empty, the handoff is refused outright with `SKIP: '<field>' already has a value (...)`, and no human is called. This never depends on the model remembering or looking carefully; the code guarantees it.

**Reasoning:** this is the same pattern as D33 (approval enforced inside the tool, not left to the model) applied to a different failure: don't ask the model to track state we can just read directly. Tested offline: a filled field is skipped with no handoff; a genuinely empty one still hands off exactly as before.

**Brief ref:** 3.1 (agent loop correctness), 3.6 (a well-reasoned handoff mechanism, not just a TODO).

### D55 — Ask for every missing field at once, not one at a time

**Question:** The agent asked for missing values field by field ("next, next, next"), a separate handoff each time. The user wants one handoff listing everything still empty, and a second one (if needed) showing only what's still missing, not the whole list again.

**Chosen:** a new tool, `request_missing_values(hints)`, replacing the field-by-field loop. It scans the current page's own element list (reusing the `value` field added in D54) for empty, visible textboxes and dropdowns, builds one message naming all of them, and opens a single handoff. Calling it again after some are filled naturally shows only what remains, because it re-scans the live page rather than remembering an old list. `request_value(ref, hint)` stays available for the single-field case; the prompt tells the model to prefer the batch tool once more than one value is missing.

**Reasoning:** the field-by-field loop cost one full model turn and one handoff per field, for no benefit: none of the earlier fields depend on a later one. A single batched ask matches how a person would actually fill out a form.

**Brief ref:** 3.6 (a well-reasoned handoff mechanism).

### D56 — Block the risky button during any handoff except the approval step itself

**Question:** During an ordinary handoff (filling in a missing field, or `ask_human`), the human has full control of the page — including the Send/Transfer button. D33's approval gate only guards the *agent's* click; nothing stopped a human from clicking Send directly while filling in an unrelated field, bypassing the gate entirely.

**Chosen:** `human_takeover(question, block_risky=True)`. When `block_risky` is true (the default), every element `needs_human` would flag is blurred and made unclickable (`pointer-events: none`, a blur filter) for the duration of that handoff, then restored on Done. The one call site that must NOT block is the takeover offered inside `click()`'s own approve/reject/take-over choice, since that takeover exists specifically so a human can act on that button; it passes `block_risky=False`.

**Reasoning:** the risk classification already exists (`needs_human`, D33/D34); this reuses it rather than inventing a second one. It closes a real gap: a human acting directly on the page was never covered by our tool-level approval, only an agent's click was. Best-effort, not absolute: it relies on the last observation's ref numbers, so a page reload mid-handoff could reset it; acceptable for a single-page form-filling flow, called out as a limit rather than hidden.

**Brief ref:** 3.4 (risky/irreversible actions handled conservatively), 3.6.

### D57 — Block the risky button during the decision bar itself, not only afterward

**Question:** D56 blocked the risky button during a later `human_takeover` (filling in a missing field). It missed the actual approve/reject/take-over decision window: while that bar is showing, the real page underneath was still fully live. A human clicked the real Send Payment button directly during that window and the payment went through, with neither an agent click nor a "take over" ever happening.

**Chosen:** in `click()`, block every element `needs_human` would flag **before** showing the decision bar, and unblock only once a decision is resolved, in a `try/finally` so an error mid-decision can never leave it stuck blocked. From there:
- **Approve:** unblocked, then our own `surface.click(ref)` performs the click. A human never touches it directly.
- **Reject:** unblocked, nothing further happens to it.
- **Take over:** unblocked, and only now, deliberately, can a human act on it themselves.

**Reasoning:** the only two paths that may ever trigger the real button are the agent's own controlled click after approval, or a human who explicitly chose to take over. Direct interaction during the pending decision itself is never one of them. Verified with a control-flow test (not a browser test) that block strictly precedes the decision bar, and unblock happens on all three outcomes.

**Brief ref:** 3.4, 3.6.

### D58 — A submitted page counts as "done" for the take-over-to-submit case

**Question:** A human took over specifically to click Send/Transfer, clicked it, and the run stayed stuck: the only hand-back signal was the separate "Done" button, and clicking Submit is not the same click as clicking Done. Nothing told the agent it could continue.

**Chosen:** `human_takeover(..., auto_on_navigate=True)`. When set, the first navigation to a **different** URL counts as done automatically, in addition to the explicit Done button. A reload of the *same* URL (e.g. a validation error re-showing the form) does not auto-resolve, since that genuinely still needs a human's attention. Only the take-over call inside `click()`'s approval decision passes this; the general form-filling takeover (`request_missing_values`, `ask_human`) does not, since navigating away there does not mean the human is finished.

**Reasoning:** the human's entire purpose for taking over at that specific point was to perform one action; the resulting page change is unambiguous evidence that they did. Requiring a second, separate click for the same intent is the friction that caused the stuck run. Verified offline: real navigation hands back immediately; a same-URL reload does not; the general takeover is unaffected either way; the explicit Done button still works in both modes.

**Brief ref:** 3.6 (a well-reasoned control-transfer model, not just a mechanism that can get stuck).

### D59 — Fix the hand-back trigger; add a whole-page lock (superseded in part by D60)

**Question:** D58's auto-hand-back was still not firing after a submit. Separately, the user asked for something broader: nothing on the page should ever be clickable or typable by a human except during an explicit handoff, not just the one risky button.

**Cause of the D58 bug:** it required the URL to change. ParaBank very likely posts a form back to the *same* URL and re-renders it with the result ("Transfer Complete!") in place, so the "different URL" check never matched. The fix: treat **any** page reload as the done signal for this specific takeover, not only a URL change.

**Chosen (replacing D56/D57's narrower mechanism):** one whole-page lock, not a per-element one.
- A full-viewport transparent overlay plus a capturing keydown/keypress blocker is active by default, driven by the same `cua_takeover` sessionStorage flag the banner already used. Locked whenever no handoff is active; unlocked only inside `human_takeover`.
- Our own injected UI (the banner, the approve/reject/take-over bar) sits on a higher z-index than the lock, so it stays usable regardless of lock state.
- Our own automated actions (`click`, `type_text`, `type_secret`, `select_option`) now pass `force=True`, confirmed to exist on all three Playwright methods before use. This bypasses Playwright's own "is the target receiving pointer events" check, which the lock would otherwise also trip for our *own* actions. `force=True` has no effect on a real human's mouse or keyboard, since those are genuine browser input events, not something routed through Playwright's API at all — the lock still stops them normally.
- ~~`click()`'s approval branch no longer computes or applies a separate risky-element block~~ **this was a mistake, corrected in D60**: it accidentally opened the risky button during every takeover, not only the approval one.

**Reasoning:** a single, general mechanism ("nothing is interactive except during a deliberate handoff") is easier to reason about and to defend than tracking which specific elements are risky at each moment, and it directly satisfies what was asked: full visibility throughout (the overlay is transparent; nothing about what's happening is hidden), zero interactivity outside an explicit handoff. Verified offline: the corrected hand-back trigger fires on a same-URL reload (the actual reported case) as well as a genuine navigation, while the general takeover and the explicit Done button are unaffected either way.

**Known limit, not yet exercised in a real browser:** whether `force=True` on `select_option` behaves as expected under the lock has not been tested live; if the lock ever interferes with our own dropdown selection, that call site is the first place to check.

**Brief ref:** 3.4, 3.6.

### D60 — Restore the risky-element block, layered under the general lock; fix a stale-flag bug

**Question:** After D59, two things broke: (1) the risky button became clickable during an *ordinary* handoff (filling a field), not only the approval one; (2) the human could click and type freely at all times, even during the agent's own turn, surviving every kernel restart.

**Cause of (1):** D59 conflated two different questions into one switch. "Is a takeover active" and "should the risky button specifically stay blocked" are not the same thing — a general takeover should open the rest of the page while still keeping that one button non-interactive. Tying both to the single lock removed the protection D56/D57 had already got right. This is a real regression, not a new design choice.

**Cause of (2):** the lock/unlock state is read from `sessionStorage`, which lives in the **browser tab**, not the Python kernel. Restarting the kernel does not close the browser Playwright launched — it is a separate process. If that flag was ever left at "takeover active" by an earlier run that hit an exception mid-takeover (several did, earlier in this session), it stays stuck at that value through any number of kernel restarts, since nothing was ever explicitly resetting it. No amount of code fixes on the Python side could have addressed this without also clearing the browser-side state.

**Chosen:**
- Restore `BLOCK_JS`/`UNBLOCK_JS` (the risky-element-specific block from D56/D57), applied **in addition to** unlocking the general page, inside `human_takeover(block_risky=True)` (the new default). Only the take-over-to-submit call site in `click()` passes `block_risky=False`.
- At the one-time browser setup, explicitly clear the `cua_takeover` (and `cua_question`) flags before doing anything else, regardless of what the tab's `sessionStorage` already holds. A fresh kernel now always starts from a known "not in takeover" state, even in a browser tab reused across restarts.

**Reasoning:** layering (general lock + a narrower risky-only block on top, removed only for the one deliberate case) is what the user actually asked for from the start; D59's single-switch version was an over-simplification that traded away correctness for tidiness. The stale-flag fix addresses a class of bug, not just this one instance: any state stored in the browser tab must be defensively reset at startup, since kernel restarts do not imply a clean browser.

**Brief ref:** 3.4, 3.6.

### D61 — force=True does not bypass a covering overlay for clicks (verified, not assumed)

**Question:** After D60, "Approve" did nothing. Why?

**Cause, verified against Playwright's own source and docs** (not reasoned from memory): `force=True` skips Playwright's own pre-click actionability *checks*, but the click is still delivered by coordinate — Playwright's own documented click sequence is "wait for actionability checks, unless force is set... use `page.mouse` to click over the center of the element." A coordinate-based mouse event is still hit-tested by the real browser exactly like a real click. If our lock overlay sits on top at that point, the overlay receives it, not the intended button. `force=True` never bypassed the lock; D59/D60 assumed it did, and that assumption was wrong.

**Chosen:** genuinely remove the lock for the instant of our own action, then restore it immediately after, via a small `_unlocked(coro)` wrapper used by `_click`, `_type_text`, `type_secret`, and `select_option`. This is scoped as tightly as possible: only the single Playwright call itself runs unlocked, not the surrounding wait/timeout logic, to keep the window a human could theoretically act in as close to zero as practical.

**Reasoning:** sidesteps the uncertainty entirely rather than depending on an assumption about how Playwright's internals interact with CSS overlays. Verified against documentation before writing, given how costly the earlier wrong assumption was.

**Open, not yet confirmed:** two further reports (nothing clickable during an active takeover; everything clickable during the agent's own turn) were not reproduced by code review alone — `SYNC_UI_JS`'s own branching was read closely and no bug was found in it by inspection. Direct print diagnostics were added around every lock/unlock transition (initial setup, takeover start, takeover end) to get real evidence rather than a further guess. Until that evidence comes back, D60's mechanism should be considered unverified in practice, not confirmed working.

**Brief ref:** 3.4, 3.6.

### D62 — Restrict a handoff to only the field(s) actually needed

**Question:** During a missing-value handoff, the whole page opened up (minus the risky button), letting a human click nav links or wander anywhere. Can the handoff instead only allow the specific field(s) that are actually missing?

**Chosen:** `human_takeover(allow_refs=[...])`. When given, the general lock (D59) stays fully active, and only the named elements are individually raised above it (z-index higher than the lock, below our own UI, matching the CSS stacking technique the lock itself already relies on), with a visible green outline marking them for the human. Everything else, including navigation, stays locked. `_ask_for_value` (used by `type_text`, `select_option`, `request_value`) passes exactly the one ref it's asking about; `request_missing_values` passes every currently-missing ref at once. `ask_human` and the take-over-to-submit case in `click()` do not use this — they genuinely don't know a single specific target in advance, so they keep the broader "everything except the risky button" or "everything" access respectively.

**Reasoning:** the tools that call `_ask_for_value`/`request_missing_values` already know precisely which element(s) need a human's input; there is no reason to expose more of the page than that. This is the same "only the graders access what they need" principle already applied elsewhere, now applied to the handoff surface itself.

**Confidence note:** this relies on CSS z-index stacking to raise an element above the lock overlay, a standard and well-documented technique, not the kind of Playwright-internals assumption that was wrong in D61. Not yet exercised in a live browser.

**Update:** first live test showed the green outline correctly, but typing into the field did nothing. Cause: the lock has two independent mechanisms, a click-blocking overlay and a *global* keydown/keypress listener on `document` that swallows every keystroke regardless of what has focus. `RESTRICT_JS` only exempted the allowed field from the click side (via z-index); the keyboard blocker had no such exemption and kept intercepting every key. Fixed: the keyboard blocker now checks `event.target.classList.contains('__cua_allowed')` and lets the event through for that element, fixed in both places the blocker is installed. This was found and fixed from direct code review of the report, not a further guess.

**Brief ref:** 3.6.

### D69 — Login attempt limit: a prompt rule, plus a code-level hard cap

**Question:** login could be retried indefinitely if it kept failing (wrong username, a genuinely nonexistent user, or a slow/flaky page). Limit it to a fixed number of tries, and stop cleanly if the login page reports the credentials are invalid.

**Chosen:** both a prompt rule and code enforcement, not just one:
- **Prompt:** "Attempt login at most 3 times. If the page says the login could not be verified, stop immediately... call finish with 'STUCK:'."
- **Code (`login_check`, a pure function, tested offline before wiring in):** every click on the Log In button counts as an attempt. If the resulting page contains a known failure phrase (best-guess wording, not verified against the live site this session: "could not be verified," "user does not exist," "invalid username or password"), it blocks immediately, on attempt 1 if needed. Otherwise, a **hard cap of 3 attempts** blocks regardless of wording. Once blocked, `click` refuses to click "Log In" again at all — the same pattern already used for a human-declined risky button (`DECLINED`).

**Reasoning:** a prompt-only rule has already been shown, more than once this session, not to reliably stop the model from retrying something it was told not to. The wording-based check is a best effort and may miss ParaBank's exact phrasing; the attempt-count cap is what actually guarantees the loop ends, regardless of whether the text match ever fires. Verified offline: a failure message blocks on attempt 1; a successful-looking page does not block; three attempts with no matching text still hits the hard cap on the third.

**Brief ref:** 3.1 (stopping conditions: max steps, dead end), Section 9 (respect the target site — do not hammer a login endpoint indefinitely).

## H. Assumptions and defaults (to confirm)

- ParaBank needs a registered **test user**; registration asks for an SSN. We use fake data, and registration is a one-time setup outside the artifacts.
- We stay polite to ParaBank: few runs, slow pace, no real data (Section 9).
- Defaults in config: 25-step limit, 3 repeats → stuck, 2 retries on slow page, $500 transfer limit and per-run cap.
- Repo layout: `src/`, `artifacts/`, `evidence/`, `config/`, `tests/`, `README.md`, `REPORT.md`, `.env.example`.
- The previous attempt is ignored entirely.

## I. Explicit cuts (feeds REPORT heading 7)

Not built, by design: operator console beyond `page.pause()`; multi-tenant plumbing and override loading; desktop or legacy-DOM surface; parked-session approval flow; image-based locator fallback; API/service wrapper; assisted LLM fallback; live end-to-end test.

Candidate stretch goals if the core is solid: the `draft → verified` approval state (already half-built by D23); multi-run stability score; agent-facing capability catalog.

## J. Open risks

- **Deep agents + Playwright fit** (D4): unverified in practice; fallback is a custom LangGraph graph with the same tools.
- **Numbered screenshot cost and covered fields** (D2, D18): tokens per step, and covered fields the model may need.
- **ParaBank availability** (D1): public server may be slow or down; evidence must be saved early.

## O. Phase 2 v2 decisions (schema simplification, agreed in conversation before build)

A simplification of the Phase 2 schema (section L, D37-D40) was agreed with the user before this
work started, and is recorded here as the decisions actually taken. Source of truth for what was
cut and what was kept is the table below, which mirrors the table agreed in conversation exactly.

| Piece | Verdict |
|---|---|
| Typed inputs/outputs, steps, checkpoint (both signals required), risk_level + per-step risk + `amount_input`, `outcome_rules` 3-way taxonomy, `secrets` as names only, `status` | KEEP, unchanged in spirit |
| Locators: ranked list of up to ~3 | SIMPLIFY to one `primary` + one optional `fallback` (D63) |
| `app.id`, `app.vendor`, `base`, `overrides` | CUT entirely (D64) |
| `routes` (a separately-maintained list) | CUT as a stored field; derived instead (D65) |
| `when_to_use` | CUT, folded into `description` (D66) |
| `tool_contract()` | KEEP the concept, adjusted for the fields above (D66) |

### D63 — Locators: one primary + one optional fallback, with a required note

**Question:** The original schema (D8, D37) ranked up to ~3 locators per target. Is that ranked
list pulling its weight, or is it more ceremony than the brief asks for?

**Options:**
- (a) Keep the ranked list of up to 3 (original D8/D37).
- (b) Exactly one `primary` locator, plus one optional `fallback`. Enforce "at most one fallback"
  by the type itself (two named fields), not by a runtime length check on a list.

**Chosen:** (b).

**Reasoning:**
- Two tries — the best-known locator, and one backup — covers the realistic case (a page redesign
  moves an element but a second, independently-stable signal usually still works) without the
  ceremony of ranking a third or fourth locator that, in practice, was never populated in either
  hand-written example artifact.
- **Enforcement is structural, not a validator:** `Target` has exactly the fields `primary` and
  `fallback: Locator | None`. There is no list to put a third locator into, so a third locator is
  **not representable** by the type at all, which is a stronger guarantee than a length check that
  could in principle be loosened later. A stray extra key on `Target` is still caught, by the
  same `extra="forbid"` base every model already uses — no new validator was needed.
- **`note` becomes required** (`Field(min_length=1)`) on every locator, not optional. This
  directly satisfies the brief's "identification with reasoning about robustness" (3.2): a
  locator can no longer be checked in with no explanation of why it was trusted.
- The ordering check (fallback must not be strictly more stable than primary) is the same rule as
  before, just comparing two ranks instead of walking a list.
- `structure` still requires `within` (no page-wide index); `labeled_value` is still extract-only.
  Both cross-checks now iterate `target.locators()` (a two-or-one-element helper list) instead of
  `target.locators`.

**Brief ref:** 3.2 ("how each target element is identified... with reasoning about robustness").

### D64 — Multi-tenant fields cut; `base_url` is the only surface fact left

**Question:** `app.id`, `app.vendor`, `base`, and `overrides` (D21, D40) existed to gesture at
multi-tenant reuse without building it. Do they earn their place in the schema?

**Options:**
- (a) Keep them as shape-checked-only fields (original D40).
- (b) Cut them from the schema entirely. Keep only what replay actually needs to know: the site.

**Chosen:** (b). `Capability` gains one field, `base_url: str`, with the same
`^https?://` pattern `App.base_url` used to carry. No wrapper object.

**Reasoning:**
- 3.7 asks that the core abstractions not "paint you into a corner", not that every future idea
  get a placeholder field today. `base`/`overrides` were validated for shape only and never
  applied (D40 said so plainly); carrying dead weight in every artifact file is not free — it is
  one more thing a human reviewer has to read past.
- Multi-tenant reuse and drift detection (D21) remain exactly what they were: a REPORT.md design
  discussion. Section 3.7 explicitly asks for design, not build, here. Nothing about the design
  argument in D21 depended on the field existing in the schema.
- A single top-level `base_url` is simpler than a one-field wrapper object (`app: {base_url:
  ...}`); with `id` and `vendor` gone there is nothing left to group.
- **Cost:** if multi-tenant override machinery is ever built, `base_url` would need to become
  either a per-tenant override input or move into a separate deployment-config file, outside the
  capability artifact. That is a schema change, honestly noted here rather than hidden behind a
  field that was never wired up anyway.

**Brief ref:** 3.7.

### D65 — `routes` derived from `navigate` steps, not stored

**Question:** The original schema stored `routes: list[str]` and cross-checked every `navigate`
step's path against it (D15's allowlist wants "the pages this capability may touch"). Is a
separately-maintained list the right way to get that fact?

**Options:**
- (a) Keep `routes` as a stored, cross-checked field (original schema).
- (b) Cut it as a stored field. Compute it on demand from the capability's own `navigate` steps.

**Chosen:** (b), via `derived_routes(cap) -> list[str]`.

**Reasoning:**
- A capability's `navigate` steps already say, unambiguously, every page it deliberately visits.
  A second, hand-maintained list saying the same thing is pure redundancy — and redundant data
  can drift out of sync, exactly the failure mode a reviewer would have to notice by hand.
- `derived_routes` returns each `navigate` step's path with its query string dropped, in
  first-appearance order, deduplicated: `derived_routes(bal) == ["/activity.htm"]`,
  `derived_routes(xfer) == ["/transfer.htm"]`.
- Whatever later phase enforces the D15 allowlist can call `derived_routes(cap)` at the point it
  needs the list, instead of trusting a field that could have been left stale after an edit.
- **Cost:** a capability can no longer declare a route it intends to use but has not yet written a
  step for (e.g. "reserved for a future step"). This was not a case either example artifact used,
  and is easy to reintroduce later as an explicit `extra_routes` field if it turns out to matter.

**Brief ref:** 3.2, 3.4 (the allowlist still gets its route list, just computed rather than typed twice).

### D66 — `when_to_use` folded into `description`

**Question:** The schema carried both `description` and `when_to_use` as separate free-text
fields, both ultimately read by the same audience (a human reviewer, or a calling agent choosing
a capability by name).

**Options:**
- (a) Keep both fields (original schema).
- (b) One field, `description`, that a capability author writes to cover both what it does and
  when to use it.

**Chosen:** (b).

**Reasoning:**
- The original `tool_contract()` concatenated them anyway (`f"{cap.description} Use when:
  {cap.when_to_use}"`), which is itself a sign the split was not doing useful work: the calling
  agent always saw them as one piece of text. Removing the split removes a place a reviewer could
  fill in one and forget the other, or duplicate the same sentence in both.
- `tool_contract()` keeps the same shape and the same job (3.2: "a calling agent can understand
  what it needs and returns"); its `description` key is now simply `cap.description`.
- **Cost:** a capability author loses the gentle structural nudge to write a distinct "when to
  use this" sentence. This is a documentation-discipline cost, not a schema-expressiveness one —
  nothing that could be said with two fields cannot be said in one paragraph.

**Brief ref:** 3.2.

### D67 — An element with no name at all: the scanner still finds it, but degrades gracefully

**Question:** D2's scan gets an element's name by trying, in order: `aria-label`, a real `<label>`,
its own button text/value, its visible text, then placeholder/title/alt/name. What happens when
*none* of those exist — the exact "no clean DOM" case the brief centers on (Section 1)?

**Checked against the actual code, not assumed:** `nameOf()` returns an empty string `''`. Nothing
raises, nothing is skipped.

**Chosen (this is a statement of existing, verified behaviour, not a new build):**
- The element is still found by the selector, still gets a number, still gets a red box drawn on
  it, still appears in the screenshot. Visibility and size are the only things that exclude an
  element (`getBoundingClientRect`/`getComputedStyle`) — an empty name never does.
- The text list shows it as `[7] textbox ""` — a number and a role, no name.
- Anywhere that turns a ref into a human-facing message (`_describe`, D53) falls back to a generic
  `"field N"` unless the model supplies its own `hint`, read visually from the screenshot.

**Reasoning:** this is not hypothetical — it is the exact mechanism behind the "field 17" bug found
and fixed in D53. The scanner's job (D2) was always to keep working with no clean markup; this
confirms the *element* keeps working (findable, numbered, actionable) even when the *name* cannot.
The visual channel (the picture) is what recovers the missing name, which is the entire argument
for the hybrid over text-only perception in D2.

**Brief ref:** 3.1 (bias toward approaches that work with no clean DOM), D2, D53.

### D68 — Two elements with the identical name: how they are told apart, and where the schema falls short today

**Question:** Two links both say "Edit" (one per row in a table). Numbering alone does not fix
this — both still need to be found again correctly on replay.

**Checked against the actual schema, not assumed:**

| Locator strategy | Has a `within` (scope to a container) field? |
|---|---|
| `role` | Yes |
| `text` | Yes |
| `label` | **No** |
| `labeled_value` | **No** |
| `structure` | Yes, and required (D8) |

**Chosen (a mix of what already works and an honestly stated gap):**
- **At discovery time, this is already handled.** Two identically-named elements still get
  different ref numbers and different on-screen positions (the picture shows *where* each one
  sits, e.g. next to which row's data). The model can pick the right one using that surrounding
  visual context even though the text list alone, read in isolation, would be ambiguous between
  them. This is the hybrid perception design (D2) doing real work, not a coincidence.
- **At replay time, it depends on which strategy was recorded.** A `role` or `text` locator can be
  scoped with `within` to "the Edit link inside this row," resolving the ambiguity. A `label` or
  `labeled_value` locator cannot be scoped at all today — if the recorded label text is genuinely
  duplicated elsewhere on the page, it is not resolvable with the current schema.
- **Not yet enforced:** nothing today requires a locator to be scoped just because its name might
  be duplicated; an under-scoped `role`/`text` locator can still be saved without error.

**Reasoning:** stating this precisely, rather than assuming duplicates are automatically handled,
avoids a false sense of robustness. The fix is recorder-side, not schema-side: the recorder (not
yet rebuilt) must check during discovery whether a candidate name/label is duplicated on the page
and, if so, either add a `within` scope or pick a different strategy. Flagged here so the recorder
rebuild plan treats "duplicate name on the page" as a required test case, not an afterthought; also
belongs in REPORT.md's cuts section as a stated limitation if the recorder rebuild does not close
the `label`/`labeled_value` scoping gap.

**Brief ref:** 3.2 (robustness reasoning per locator), 3.7 (heterogeneous, legacy surfaces are
exactly where duplicate or ambiguous labels are common).

## P. Phase 3 v2 decisions (the recorder, rebuilt against D63-D69)

The Phase 3 recorder (section M, D41-D49) targeted a schema and a set of agent tools that no
longer exist by the time this rebuild started: `Target(locators=[...])` (a ranked list) instead of
`primary`/`fallback` (D63); `Capability(app=..., when_to_use=..., routes=...)` instead of a single
`base_url` (D64-D66); and browser tools from before every Phase 1 safety fix built through live
testing (D50-D69: the whole-page lock, the approval gate inside `click()`, `request_missing_values`,
the login attempt guard). Running the old recorder's compile step against the live schema raised a
Pydantic error immediately, and the old capture half had never been run against a real browser (0
of 33 cells with a nonzero `execution_count`). D41-D49 above are marked superseded individually,
with the specific code-shape break named at each. This section records what was actually built.

### D70 — Reuse the exec-cells-into-namespace technique for both halves

**Question:** How does the compile half import the CURRENT Phase 2 models, and how is a genuine
offline test run proven, given the CAPTURE half needs a real browser and this agent must not
launch one?

**Chosen:** `load_schema()` execs `02_artifact_schema.py`'s non-check cells into this notebook's
namespace -- the exact technique `04_replay_engine.py` already uses, not a new one. To prove the
COMPILE half offline, a harness (not part of the committed notebook) execs only the
`OFFLINE`-prefixed cells of `03_recorder.py` by splitting on `# %%` and filtering by header, the
same split-by-cell-header approach `load_schema()` itself uses one level up.

**Reasoning:** consistency with the existing repo pattern beats inventing a second import
mechanism. One sharp edge, found and fixed during this build: `exec(code, ns)` with a bare `ns`
dict lacking a `__name__` key breaks Pydantic's discriminated-union validation for a model
constructed from already-built instances (`Target(primary=RoleLocator(...))` raised
`model_attributes_type` errors), because class `__module__` resolution during `exec` depends on
`__name__` being present in the exec globals. `02_artifact_schema.py`'s own `load_schema()` never
hits this (it execs into the real running script's `globals()`, which already has `__name__`);
the offline test harness must set `ns = {"__name__": "__main__", ...}` explicitly, or the exact
same construction pattern `04_replay_engine.py` uses (and passes) fails when isolated into a bare
dict. Recorded here since it cost real debugging time and would bite anyone building a similar
harness later.

**Brief ref:** 3.2, 3.3, code quality.

### D71 — Locator derivation against `primary`/`fallback`, with D68's gap tested for, not closed

**Chosen:** `derive_target(el, inputs, warnings) -> Target` builds one ranked list of candidates
(role > label/text > structure) and takes the first two as `primary`/`fallback` (D63's shape).
Duplicate names (D68): a `role`/`text` locator whose name is not unique on the page is scoped with
`within` when a container was captured; with no container, it is saved unscoped and the compiler
appends a warning to the report rather than inventing a container that was never observed. A
duplicated `label` (or, for `extract`, `labeled_value`) has no `within` slot on the schema at all
(D68's own stated gap) and is refused outright with `CompileError`, never silently saved ambiguous.

**Reasoning:** this is D42's original reasoning, rebuilt against the current `Target` shape, plus
the concrete fix D68 asked for ("the recorder... must check during discovery whether a candidate
name/label is duplicated... and, if so, either add a `within` scope or pick a different strategy").
The unscoped-but-no-container case is a judgment call, made explicit here rather than left
implicit: refusing outright would make an honest recording impossible whenever the capture half
could not observe a container (a real limit of the DOM, not a recorder bug), so it is flagged
instead. The `label`/`labeled_value` case has no such escape hatch (the schema has no field to put
a scope in), so it is refused, matching D68's honestly-stated gap exactly -- this rebuild does not
close that gap, only detects and reports it, as D68 itself says is the recorder's job.

**Brief ref:** 3.2, 3.7, D68.

### D72 — The event shape, and where each field actually comes from

**Chosen:** one event dict per real tool call: `{i, tool, args, message, status, before, after,
approved, el, value, label, save_as, value_type, description, outcome, proof, summary, values}`.
`status` is computed by `classify_status(message)`, a pure function bucketing the EXACT prefixes
read directly out of agent.ipynb's STEP 3 code (`DENIED:`, `DECLINED`, `BLOCKED:`, `SKIP:`,
`NOT YET:`, `STOP:`, the `CLICK/TYPE/SELECT FAILED`/`UNKNOWN SECRET`/`REFUSED:` failure family, and
an `"A human "`-prefixed success text for every handoff path -> `handoff`). `el`'s richer fields
(`label`, `container`, `nth`, `name_count`, `label_count`) come from a new, additive
`DESCRIBE_JS`, called only when logging an event, never shown to the model and never touching
`OBSERVE_JS` (copied verbatim). `DESCRIBE_JS`'s own `roleOf`/`nameOf` intentionally duplicate
agent.ipynb's `OBSERVE_JS` logic in a few lines, so "name" means the same thing to the recorder as
it does to the model; this duplication is documented in the notebook, not accidental.

**Reasoning:** classifying status from real, verified message prefixes (not guessed text) is what
makes clean-up (D43) and the top-level refusals (D70's harness proved these against fixtures shaped
from the real prefixes) trustworthy. Keeping the richer descriptor computation entirely separate
from `OBSERVE_JS` is what makes the "never touching a tool's own body" claim literally true rather
than aspirational.

**Brief ref:** 3.2, 3.3, code quality.

### D73 — Two new tools and a wrapper, not a rewrite: `extract_value`, `open_path`,
`finish_business_outcome`, and the `.coroutine` capture wrapper

**Chosen:** every tool in `BROWSER_TOOLS` (copied verbatim from agent.ipynb) plus `open_path` gets
its `tool_obj.coroutine` replaced by a wrapper that logs `before`/`el`/`args`, calls the ORIGINAL
coroutine unchanged, logs `after`/`message`/`status`, and returns the original result unmodified.
`extract_value` (reads a value shown next to a label, checks its declared type, never logs the
value itself, D46), `open_path` (GET-navigate within the allowed host, same deny-word and
value-grounding checks as `click`/`type_text`, D47), and `finish_business_outcome` (refuses unless
`proof_text` literally appears on the page, records `outcome`/`proof` for `rule_from_probe`, D47)
are three small, separately-defined new tools -- `finish` itself is never modified to add
`outcome`/`proof_text` fields, since that would be respelling a copied tool rather than adding
alongside it.

**Reasoning:** `.coroutine`-wrapping is the literal mechanism the task asked for ("wrap the
relevant tools... without changing any tool's existing behavior or return value"): the agent
framework calls each tool the same way whether or not it is wrapped, and unwrapping is a one-line
revert (restore the saved `_original` reference) if this ever needs to be undone. A new tool next
to `finish`, rather than a modified `finish`, keeps the "copied verbatim" claim about agent.ipynb's
own tools literally true.

**Brief ref:** 3.2, 3.4, D46, D47.

### D74 — Top-level refusals run before any clean-up, and refuse the WHOLE run, not one step

**Chosen:** `compile_run` checks, before touching clean-up at all: any event with `status ==
"stop"` (D69's login attempt guard fired) refuses with a message naming D69 explicitly; any event
with `status == "handoff"` refuses (a hand-typed step cannot be recorded, D43); a `finish` event
whose `summary` starts with `STUCK:` or `DECLINED:` refuses; a run whose terminal event is
`finish_business_outcome` refuses (it is a probe, use `rule_from_probe`, not `compile_run`). Each
is a hard rule stated as its own hard requirement, not a review-warns to be worked around.

**Reasoning:** the assignment's own hard rule ("a run blocked by the login attempt guard... must
never be compiled into a capability at all -- refuse clearly") is unambiguous, and the cleanest way
to guarantee it is to check it before any other logic runs, rather than hoping clean-up's ordinary
drop rules happen to remove every trace of a bad run. Fixture 8 (offline, hand-made `STOP:` event)
proves this refuses immediately, before clean-up, login-split, or step-building ever run.

**Brief ref:** 3.4, 3.6, D69.

### D75 — Offline fixtures are hand-built from real message prefixes, run via a cell-filtering harness

**Chosen:** every offline fixture's events are built with a small `_e(...)` helper from the exact
message strings agent.ipynb's tools return (e.g. `"STOP: login failed (login was attempted 3 times
with no success)..."`, verbatim from STEP 3's own `click()` body), not invented text. All fixtures
and their assertions live in `OFFLINE`-titled cells inside the committed notebook itself (not a
separate test file); a temporary, uncommitted harness (matching D70) execs only those cells to run
them with `uv run python`, proving the compile half end to end with zero browser code touched.

**Reasoning:** the brief's own worry ("a run of hand-made fixtures that don't look like what a real
tool actually returns") is closed by sourcing every fixture's text from the real tool code, not
from what compile code is convenient to test. Keeping fixtures inside the shipped notebook (rather
than a separate `tests/` file, which does not exist in this repo's layout) matches this project's
existing convention (`02_artifact_schema.py`, `04_replay_engine.py` both do the same).

**Brief ref:** Section 6 (README: how to run without live services), Section 7 (code quality).

### D76 — TypeSafe added to the recorder's capture agent, at the user's explicit request

**Question:** agent.ipynb's `STEP 3d`/`STEP 3e` (TypeSafe `Choice` tool-selection, D52) and the
TypeSafe half of `STEP 4` (the Haiku/Sonnet model router, D50) were initially left out of the
rebuilt recorder's capture half (original reasoning: optional third-party performance layer, not a
safety mechanism, not needed to prove the compile pipeline). The user pushed back directly: "add
it, it['s] a major part of the agent." Should the recorder's capture agent match agent.ipynb here?

**Options:**
- (a) Leave it out, as first built. Matches "not a safety mechanism" reasoning, but the recorder's
  capture agent would then behave differently from agent.ipynb in a way the user considers
  significant, not marginal.
- (b) Copy `STEP 3d`/`STEP 3e`/the TypeSafe half of `STEP 4` verbatim, exactly as every other
  agent.ipynb cell in the capture half already is.

**Chosen:** (b).

**Reasoning:**
- The user's own framing ("a major part of the agent") overrides the earlier judgment call that
  it was a minor, skippable extra. Both stay **off by default**, unchanged from agent.ipynb: only
  `TYPESAFE_API_KEY` in `.env` activates either layer, so the default (no-key) capture run behaves
  exactly as before this change.
- **One small, additive, clearly-labelled extension was still necessary, not optional:**
  agent.ipynb's own `JOB_EXTRA_TOOLS` mapping (four job categories) predates `request_missing_values`
  (D55) and, in this notebook specifically, also predates the three new tools this rebuild adds
  (`extract_value`, `open_path`, `finish_business_outcome`, D73) — none of the four job categories'
  criteria mention them. Left alone, an active, confident TypeSafe classification of any job could
  silently strip these tools from what the model is offered, mid-capture, defeating their purpose.
  The fix is the same one D52 already committed to for exactly this situation ("never removes the
  always-allowed set"): these four tool names are folded into `NEVER_HIDE`. `JOB_EXTRA_TOOLS` and
  `JOB_CRITERIA` themselves are untouched — copied verbatim, not respelled.
- **A real, pre-existing bug in agent.ipynb was found and fixed in this copy, not in agent.ipynb
  itself:** `STEP 3e`'s own offline check asserts `confidence_gate(_ALL, "fill_form", 0.75) ==
  NEVER_HIDE | {"type_text", "select_option"}`. This is mathematically false as written: `0.75 <
  JOB_CONFIDENCE_THRESHOLD` (`0.8`), so `confidence_gate` fails OPEN at that confidence and returns
  the full tool set unchanged, not a narrowed one. Verified directly by running agent.ipynb's own
  `confidence_gate` with these exact values, not assumed. agent.ipynb's own `.ipynb` shows no
  executed output for this cell (unlike the cells immediately around it), consistent with this
  assertion never actually having been run for real. agent.ipynb is read-only for this task, so the
  bug is not fixed there; this notebook's own copy of the same check uses `0.85` instead, since
  this notebook actually executes its offline checks with `uv run python` and a false assertion
  would silently break "ALL OFFLINE CHECKS PASSED".
- Verified offline (no network, no key): `job_tool_names`/`confidence_gate` behave exactly as
  agent.ipynb's own STEP 3e checks require (with the one corrected value above), and the D76
  extension itself is checked directly -- all four of the new/predating tools survive
  `confidence_gate` under every job category, confident or not.

**Brief ref:** 3.1 (agent loop correctness), 3.4 (the D50/D52 redaction caveat applies here
unchanged: step text and page state leave the process to `api.typesafe.ai` whenever this is on).

## Q. Phase 4 live wiring (async mirror + real browser, D77-D80)

### D77 — A parallel async engine, not a converted one, plus two factored pure helpers

**Question:** `04_replay_engine.py`'s `run_capability`/`ReplaySurface` are entirely sync (11+
tests passing). `agent.ipynb`'s real browser control is entirely `async` (Playwright's Python API
has no sync mode usable inside a Jupyter kernel, which already runs its own asyncio event loop --
bridging with `asyncio.get_event_loop().run_until_complete(...)` breaks with "this event loop is
already running"). How does replay reach a real browser without breaking the already-verified sync
path?

**Options:**
- (a) Convert `run_capability`/`ReplaySurface` to async in place.
- (b) Add a parallel `run_capability_async`/`AsyncReplaySurface`, leaving the sync engine
  untouched.

**Chosen:** (b).

**Reasoning:**
- (a) would touch every existing test (8 required scenarios + 3 bonus + the Section 5 integration
  check against both real example artifacts) for no functional gain to the sync path, which has
  no async caller and does not need one -- only the live notebook does.
- `run_capability_async` is a genuine mirror, not new business logic: same input validation, same
  primary-then-fallback resolution order, same risky-click gate checked BEFORE the click, same
  outcome-rule order (first match wins), same bounded retries (never for a risky click), same
  checkpoint/output checks, same four `ReplayResult` statuses. Verified by running the whole file
  (`uv run python notebooks/04_replay_engine.py`) after every edit: all prior sync output lines
  are unchanged, immediately followed by their async twins.
- Two PURE (no surface call, no escalate call) helpers were factored out of the sync cells rather
  than hand-copied into the async ones, so the two engines cannot silently disagree:
  `_target_locators(target)` (which locator to try, in which order -- used by both
  `resolve_target` and `resolve_target_async`) and `_find_outcome_rule(cap, url, text)` (which
  outcome rule matches first -- used by both `_check_outcomes` and `_check_outcomes_async`). Both
  refactors are behavior-preserving: confirmed by re-running the full sync suite immediately after
  each change, before adding anything new.
- **The one genuine behavioral asymmetry:** `run_capability_async` awaits `escalate(reason, ctx)`'s
  return value if it is awaitable (`inspect.isawaitable`, via a small `_call_escalate` helper). A
  plain sync fake (every existing/offline test) returns `None`, which is not awaitable, so this is
  a complete no-op for every prior test. This is not treated as a "business logic" change because
  it changes nothing about *what decision* the engine makes or *when* -- it only lets a real,
  inherently-awaitable human decision (showing a decision bar and waiting for Approve/Reject/Take
  over) finish before the function returns, which is the entire reason this mirror exists for
  `notebooks/05_replay_live.py` to be useful at all. Without it, `escalate` would have to be
  fire-and-forget (`asyncio.create_task(...)`), and `run_capability_async` could return
  `NEEDS_APPROVAL` to a notebook cell before the human had even seen the decision bar.
- Offline tests for the async mirror stay entirely offline (`AsyncFakeSurface`, an async twin of
  `FakeSurface`; no `import playwright`), run with `uv run python` via a small
  `asyncio.run(main())`-style wrapper per test group, matching the repo's existing script-cell
  convention.

**Brief ref:** 3.3 (replay, no LLM in the loop), 3.7 (the Surface seam scales to a second
implementation), code quality (no drift between two copies of the same decision logic).


### D78 — Live locator resolution for all 5 strategies, reusing the recorder's own descriptor JS

**Question:** `PlaywrightReplaySurface.resolve(locator)` must turn a saved `Target`'s `role` /
`label` / `text` / `structure` / `labeled_value` locator back into a real, clickable/readable
element on a live page. What live-page mechanism does each strategy use?

**Chosen:** reuse, not reinvent, what `03_recorder.py` already built and tested for the same
purpose (D71/D72): run `OBSERVE_JS` (`agent.ipynb`'s own numbered scanner, unmodified) to number
every visible element and set `data-cua-ref`, then call `DESCRIBE_JS` (`03_recorder.py` BROWSER 8,
copied verbatim) per candidate ref to get its role, name, label, container, nth, and visible text.
Matching per strategy:
- `role`: `descriptor.role == locator.role and descriptor.name == locator.name`; if `locator.within`
  is set, also require `descriptor.container.role == within.role` and (`within.name is None or
  descriptor.container.name == within.name`) -- the same container-matching D71 already reasoned
  about for the recorder's own duplicate-name scoping.
- `label`: `descriptor.label == locator.label`. No `within` slot exists on this strategy (D68's
  own stated gap), so this cannot be scoped; the first matching descriptor wins, same ambiguity
  the recorder already documents and refuses to silently paper over at record time (not
  newly introduced, not closed, here either).
- `text`: `descriptor.text == locator.text` (only set on non-form-control elements), with the same
  optional `within` container check as `role`.
- `structure`: container match (role + optional name) AND `descriptor.tag == locator.tag` AND
  `descriptor.nth == locator.nth`.
- `labeled_value`: NOT resolved via the numbered scan at all -- `READ_LABELED_JS`
  (`03_recorder.py` BROWSER 8, copied verbatim, the exact function `read_labeled_value` already
  uses) is called directly with the locator's label. If it finds a value, `resolve` returns a
  `LabeledValueRef(label=...)` marker (not a numbered ref) rather than inventing a fake ref number,
  since D46 already decided a labeled-value read should never depend on page position.
- No match on any strategy: `resolve` returns `None`, exactly like `FakeSurface.resolve` does for
  an unregistered locator -- `resolve_target_async`'s own primary-then-fallback loop and
  `ResolutionError`-with-both-locators-named behavior (Section 8/9, D77) does the rest, unchanged.

**Reasoning:** `DESCRIBE_JS`/`READ_LABELED_JS` were built in the Phase 3 v2 rebuild specifically so
"name"/"label"/"container" mean the same thing to the recorder as they do to a locator saved by
it; using anything else here (e.g. a fresh, second implementation of "find the container") would
risk the live replay side disagreeing with what the recording side meant when it saved the
locator. This is the task's own instruction ("reuse or closely mirror... do not invent a third
way") applied literally, not just in spirit.

**Cost / honestly-stated limits:**
- `resolve` calls `DESCRIBE_JS` once per numbered candidate element (O(n) round trips to the page
  per `resolve` call, each itself O(n) internally for `DESCRIBE_JS`'s own duplicate-count
  computation). Fine for a real login/form page (tens of elements), not scaled for a page with
  hundreds. Not optimized here; flagged for whoever revisits this once a real page is measured.
- `OBSERVE_JS`'s own selector (D2, unmodified) only numbers interactive-ish elements (`a[href]`,
  `button`, `input`, `select`, `textarea`, `[role=button]`, `[role=link]`, `[onclick]`) -- by
  design, since its job is finding things a person can act on, not general text extraction. A
  `text`-strategy locator whose recorded target is plain, non-interactive page text (e.g. a bare
  `<h1>`/`<span>` confirmation heading with no surrounding link/button/onclick, which is exactly
  what `transfer_funds.yaml`'s own `confirmation` extract step declares) will not be found by this
  scan-based `resolve`, because it was never numbered in the first place. This was not discovered
  by running a real page (never done here, by the hard rules) -- it follows directly from reading
  `OBSERVE_JS`'s selector string, and is stated honestly rather than assumed away. The task's own
  instruction was to match `text` locators "against the freshly-scanned elements," so this is
  implemented exactly as directed; whoever next runs this notebook against a real
  `transfer_funds` replay should treat this as the first thing to check if that one extract step
  reports `FAILED` with both locators unresolved, and, if so, either widen `OBSERVE_JS`'s selector
  (a schema-neutral fix) or give `resolve` a second, non-scan-based path for a bare `text` search
  of the whole page (closer to how `READ_LABELED_JS` already searches broadly for `labeled_value`).

**Brief ref:** 3.2 (locator robustness reasoning), 3.7 (heterogeneous surfaces), D2, D46, D68, D71.

### D79 — Wiring `escalate` to the real decision bar, and what a `NEEDS_APPROVAL` result can mean now

**Question:** `run_capability_async`'s risky-click branch calls `escalate(reason, ctx)` then
unconditionally returns `NEEDS_APPROVAL` -- it never resolves the target first, and never consults
`escalate`'s return value (D77: this is the sync engine's existing, untouched behavior, not
something this task may change). How does a live `escalate` let an approved click actually happen,
consistent with D28's design intent ("hold the browser open in the same session, hand back so the
run resumes")?

**Chosen:** `make_escalate(cap)` returns an async `escalate(reason, ctx)` that, for the risky-click
case (`ctx["step_index"]` names the pending step), resolves that step's target itself (via
`resolve_target_async` against the same live surface) and shows the identical Approve/Reject/Take
over bar `agent.ipynb`'s own `click()` tool already shows (`DECISION_JS`, `approval_info`'s
`{title, details}` shape, copied verbatim). On the human's choice:
- **Approve:** `await live_surface.click(ref)` -- the click happens for real, through the surface,
  the same call path any other click uses.
- **Reject:** no action. Nothing further happens on the page.
- **Take over:** `await human_takeover(question="", auto_on_navigate=True, block_risky=False)`,
  identical to `agent.ipynb`'s own take-over-to-submit call site.

`run_capability_async` itself still returns `NEEDS_APPROVAL` in every one of these cases (its own
logic is unchanged, per D77's hard rule) -- the resolve-and-click happens as a side effect inside
`escalate`, not by the engine resuming its own step loop.

**Reasoning:** D28 already chose "hold the browser open in the same session, human acts, hands
back" over a resumable cross-process flow, and explicitly deferred the actual wiring to this
phase. Making `run_capability_async` itself consult `escalate`'s return value and continue its own
loop would be a real, non-reversible business-logic change to an engine this task's hard rules say
must stay identical to the sync one. Letting `escalate` act directly keeps that promise: the
session genuinely stays open and the click genuinely happens in it (satisfying 3.6's "same live
session, not a fresh one"), while the *returned status* stays an honest description of what the
engine's own step loop did (it stopped before the click), not of what a side channel did
afterward.

**Honestly-stated limitation:** a caller reading only `result.status == "NEEDS_APPROVAL"` cannot
tell, from the `ReplayResult` alone, whether the human approved (and the click already fired) or
rejected. Distinguishing the two requires reading `escalate`'s own side effects (the live page, or
whatever the notebook prints), not the typed result. Closing this properly needs a fifth status or
a resumable engine loop -- a real schema/engine change, out of scope here, and named as a concrete
next step rather than hidden.

> **Update: corrected, see D85.** The design above let `escalate` perform the click itself as a
> side effect on Approve, while `run_capability_async` unconditionally kept returning
> `NEEDS_APPROVAL` regardless of Approve or Reject -- meaning a real payment could go through with
> no distinguishing signal in the typed result at all (worse than the "honestly-stated limitation"
> above states: Approve and Reject were not just hard to tell apart, they were byte-identical in
> the returned `ReplayResult`), and the capability's own remaining steps (an `extract` reading the
> confirmation, the final `checkpoint`) were never reached even on a genuine Approve. D85 has the
> engine itself perform the click and continue, once `escalate`'s return value says `"approve"`;
> `escalate` no longer touches the page for this branch at all. (Note on numbering: D82-D84 were
> taken by concurrent Phase 3 work landed in this same repo while this fix was being written; this
> decision continues from D84, the highest number at commit time.)

**Brief ref:** 3.4, 3.6, D20, D27, D28, D33, D58.

### D80 — `navigate`'s off-allowlist check raises a plain exception, not a `ReplayResult`

**Question:** D15 says off-allowlist navigation must be "a hard failure, never silently ignored,"
re-checked in replay. `run_capability`/`run_capability_async`'s step loop only catches
`ResolutionError` and `TransientFailure` (D77: unchanged, by this task's own hard rule) -- every
other exception propagates uncaught. Should `PlaywrightReplaySurface.navigate` raise one of those
two, or something new?

**Chosen:** raise a plain, clearly-named exception (not `ResolutionError` or `TransientFailure`,
since neither means "policy blocked") when `host_allowed(...)` is false, and let it propagate
uncaught out of `run_capability_async`, exactly as any other unexpected exception would today.

**Reasoning:** the engine's own exception contract has no third bucket for "hard-stop-but-not-a-
step-failure" today; adding one (a new caught exception type, plus a `ReplayResult` shape for it)
would be a real, non-reversible change to the shared engine's business logic, which this task's
hard rules forbid making as a side effect of live-wiring one surface. A `Capability`'s `base_url`
is already schema-checked (D64) and every `navigate` step's path is fixed at record time, so this
should never actually trigger against a well-formed artifact; if it ever does (a tampered or
hand-edited artifact), failing loudly with an uncaught exception is still strictly better than
silently navigating off-host, which is the one thing D15 forbids outright.

**Cost, honestly stated:** unlike every other kind of hard failure in this engine, an off-host
navigation does not currently produce a `FAILED` `ReplayResult` with step/expected/observed detail
-- it crashes the calling process. Flagged as a real gap, not fixed here; the fix (a new caught
exception + a documented fifth reason string, or folding it into `ResolutionError`'s family) is a
schema/engine decision for whoever next touches `run_capability`'s shared exception contract.

**Brief ref:** 3.4, D15, D77.

### D81 — `read_value`'s form-value-then-visible-text fallback

**Question:** `Extract` steps resolve to two different kinds of live targets: a form control read
via `role`/`label`/`structure` (none of the two example artifacts actually do this, but the schema
allows it), or a non-form element read via `text` (`transfer_funds`'s confirmation heading) or via
`labeled_value` (`get_account_balance`'s balance). `read_value(ref)` has to return the right kind
of live value for whichever one actually resolved, without the caller telling it which strategy
was used to find `ref` (the `AsyncReplaySurface` contract only passes a `ref`, not the locator that
produced it).

**Chosen:** for a `LabeledValueRef` marker (D78), call `read_labeled_value` again -- the exact
mechanism the recorder already uses. For a plain numbered `ref`, read the live form value first
(`current_value`, agent.ipynb's own function, copied verbatim); if that comes back empty (the
element is not a form control, or genuinely has no value), fall back to the element's own live
`innerText`.

**Reasoning:** `current_value` already handles the only two live form-control cases that matter
(`<select>`'s selected option text, `<input>`/`<textarea>`'s `value`) and is the exact function
`agent.ipynb` itself relies on elsewhere for the same idea ("what does this field currently show").
Reusing it here rather than re-deriving the same two branches keeps one source of truth for "how do
we read a form control's live value." The `innerText` fallback is new (agent.ipynb never needed it,
since it only ever reads whole-page text via `page_text`, never one element's text by ref) but is a
single, obvious line, not a second parallel value-reading system.

**Cost, honestly stated:** an empty form value (a genuinely blank input) and "not a form control"
are indistinguishable to this fallback -- both fall through to `innerText`, which for a real empty
`<input>` returns `''` anyway, so the two cases happen to coincide harmlessly for every case this
notebook's two example artifacts exercise. A form control that is both empty AND has visible child
text (unusual, but not impossible for a custom-styled input) could read incorrectly; not a case
either bundled example hits, flagged rather than special-cased blindly.

**Brief ref:** 3.2, D46, D78.

## Q. Phase 3 bugfix: a request_value/request_missing_values handoff is now recordable

A real bill-pay discovery run filled 4 fields via `type_text`, then called
`request_missing_values` because more fields were still empty. A human filled a text field
("Nagarjuana", a payee name) and a dropdown ("12345", an account) by hand during the takeover. The
run finished for real in the browser -- an actual $20 payment went through -- but `compile_run`
refused to compile ANY capability from it: "a human entered a value by hand during this run. That
step cannot be recorded." D70-D76's rebuild never distinguished a handoff with a KNOWN, specific
target from one with none at all. See
`docs/superpowers/plans/2026-09-26-recorder-human-entry-fix.md` for the full plan. (Note on
numbering: D77-D81 were taken by concurrent Phase 4 work landed in this same repo while this fix
was being written; these decisions continue from D82, the current highest number at commit time,
confirmed against `git log` immediately before writing this section, not against an earlier read.)

### D82 — `request_value`/`request_missing_values` handoffs are now recordable; `ask_human` and a take-over click are not

**Question:** `_refuse_bad_run` treated every `status == "handoff"` event as an unrecoverable gap
in the recording, with no exceptions (D74). Is that still the right rule now that CAPTURE can
(task below) turn some handoffs into a proper synthetic step?

**Options:**
- (a) Keep the blanket refusal. Simple, but wrong: it throws away a run that finished for real,
  over a step we can now fully reconstruct.
- (b) Narrow the refusal to only the handoffs where we genuinely cannot know what a human did:
  `ask_human` (free-form -- "figure out what's needed") and a take-over click (the `choice == "t"`
  path inside `click()`, D56-D62 -- the human could have done anything to the page). Everything
  else about a `request_value`/`request_missing_values` handoff is, by construction, NOT free-form:
  both tools call `human_takeover(..., allow_refs=[...])` with a specific, already-known ref (or
  list of refs) -- `request_value` passes exactly the one ref it's asking about; `request_missing_
  values` computes its list itself via `missing_field_labels(surface.last_elements, hints)` before
  handing off. `current_value(ref)` (agent.ipynb, copied verbatim) reads exactly what ended up in
  that field, whoever put it there.

**Chosen:** (b). `UNSTRUCTURED_HANDOFF_TOOLS = {"ask_human", "click"}`; `_refuse_bad_run` only
refuses a `"handoff"` event whose `tool` is in that set.

**Reasoning:**
- The distinction is not "was a human involved" (both kinds involve a human) but "do we know,
  independent of asking the model, exactly which element(s) they could have touched." A
  `request_value`/`request_missing_values` handoff answers that question by construction (the
  `allow_refs` list IS the answer); `ask_human` and a take-over click do not and structurally
  cannot -- their entire reason to exist is that no specific target is known in advance.
- This does not weaken D43's original promise ("a hand-typed step cannot be recorded"). It was
  never actually true that a `request_value` step was "hand-typed with no record" -- the code
  already knew precisely which ref was opened. The old rule was a blanket approximation that
  happened to be safe (never recording something we couldn't verify) but also happened to be
  needlessly destructive for the one case where verification IS possible.
- Kept the audit event itself unchanged (the "handoff" event `request_value`/`request_missing_
  values` produce is still appended, still classified `"handoff"` by `classify_status` -- nothing
  about `classify_status` or the event's own `status` field changes). What changes is only which
  `tool` names' handoff status is treated as fatal. This is a smaller, more precise change than
  rewriting `classify_status` to distinguish the two cases by message text, which would be brittle
  (both message families start with `"A human"` on purpose, D53).
- `clean_events` needed no change: the audit event's `tool` (`request_value`/`request_missing_
  values`) is not in `ACTION_TOOLS`, so it is already dropped as "not an action" during clean-up,
  exactly as it always was -- only the synthetic event (D83) becomes a step.

**Verified offline:** `ask_human`'s handoff still refuses, both at `_refuse_bad_run` directly (its
own updated message, `"no specific field known"`) and end to end through `compile_run` (a fresh
fixture, not only the pre-existing lower-level check). A take-over click's handoff refuses the
same way (a case the original test never covered). A `request_value`/`request_missing_values`
handoff does NOT refuse at `_refuse_bad_run`, checked directly.

**Brief ref:** 3.6 (a well-reasoned handoff mechanism, not a blanket one), D43, D53, D56-D62.

### D83 — How a synthetic event is built, and why the element's `role` decides `type_text` vs `select_option`

**Question:** Once a handoff is known to target specific ref(s), how does "the human put a value
in this field" become an event `compile_run` can turn into a step?

**Chosen:** a new pure function, `synthesize_human_entries(i_start, before_url, before_heading,
after_url, after_heading, entries)`, where `entries` is `[{"ref", "el", "value_after"}, ...]` --
one per ref that was opened for the human. For each entry whose `value_after` is non-empty, it
builds ONE event in the exact shape `_capture`'s generic wrapper already produces (`i, tool, args,
message, status, before, after, approved, el, value`), plus two new keys: `human_entered: True` and
`why` (D84). The `tool` is chosen by `el["role"]`: `combobox`/`select` -> `select_option`-shaped
(`args: {ref, option}`, matching how a real `select_option` call is logged); anything else ->
`type_text`-shaped (`args: {ref, text}`, matching a real `type_text` call). `status` is always
`"ok"`: the value is now genuinely sitting in the field, exactly as if the agent itself had typed
or chosen it. An entry whose `value_after` is still empty is SKIPPED entirely -- not synthesized,
and does not consume an `i` -- because the human declined to fill that field, and there is nothing
to record; a still-missing declared input surfaces normally at compile time (an unused input, or a
capability that fails validation), not as a special case inside this function.

**Reasoning:**
- Reusing `el["role"]` (already computed by `DESCRIBE_JS`, D72) to decide the tool, rather than
  adding a new signal, means the synthetic event is indistinguishable, at every point downstream
  (`clean_events`, `drop_detours`, `build_steps`, `derive_target`), from an event the agent's own
  `type_text`/`select_option` would have produced for the identical field. `build_steps`'s existing
  `select_option` branch already validates `e["value"] in el["options"]` -- this check applies
  unchanged to a synthetic event too, since `el` is the SAME descriptor `DESCRIBE_JS` would have
  produced for that element regardless of who filled it in.
- `i_start`/sequential numbering (not a fixed offset) lets the CAPTURE wrapper (D82's task 2) chain
  these onto `EVENTS` with `len(EVENTS)` at call time, exactly like every other event append in the
  file already does -- no new numbering scheme.
- Kept genuinely pure (no `page`, no `await`, no import beyond what OFFLINE cells already have) so
  it is testable with hand-built fixtures the same way every other COMPILE-half function is (D75).
  All page access (`current_value(ref)`, `describe_ref(ref)`) stays in the CAPTURE-half wrapper,
  which builds `entries` before calling this function.

**Verified offline (OFFLINE 4d):** one text field; one dropdown; two of each in one call
(sequential `i`, correct tool per entry); an entry left empty after handoff (skipped, no event, no
`i` consumed); `i` numbering confirmed to continue correctly from `i_start` including across a
skipped entry in the middle of the list.

**Brief ref:** 3.2, 3.3 (a synthetic event must be indistinguishable, to the compiler, from a real
one), D42, D63, D72.

### D84 — A human-entered step carries a `why` note for reviewability; D29/D44 are unmodified

**Question:** A reviewer reading a compiled capability's YAML should be able to tell that one
specific step's value was entered by a human during discovery, not decided by the agent (3.2). And:
does making these values recordable at all risk quietly weakening D29/D44's leftover-literal
refusal or constant reporting for exactly the values that most need scrutiny (ones nobody typed
into the goal)?

**Chosen:**
- `HUMAN_ENTRY_WHY = "Value entered by a human during discovery; the agent did not have this
  value."`, set as `synthesize_human_entries`'s own `why` key (D83) and copied onto the compiled
  `TypeText`/`Select` step by `build_steps` whenever `e.get("human_entered")` is true -- the exact
  same `why` field a risky `Click` step already uses for its own reviewer-facing note ("Point of no
  return..."), not a new mechanism.
- D29/D44 (`find_leftovers`, `_params`'s constant reporting) are **not modified at all**. Both
  already operate on the compiled `Capability`/a typed value alone, blind to which tool produced
  the underlying event -- there was never a `human_entered` check to add one to.

**Reasoning:**
- Reviewability (3.2) is served by making the fact visible on the step itself, in the same place a
  reviewer already looks for "why is this here" (the risky-click note), rather than a separate log
  or comment a reviewer would have to know to go find.
- The real risk this decision addresses is a DIFFERENT one: it would be easy, when making these
  values recordable, to also (accidentally or "helpfully") skip D29/D44's checks for them, on the
  theory that "a human already saw this value, so it's fine." That reasoning is wrong -- a
  human-entered value that leaks into an unparameterized part of the capability, or that silently
  becomes a hard-coded constant, is exactly as much of a replay-fragility risk as an agent-typed
  one, arguably more so (nobody declared it as an input, so nobody is thinking about it as
  variable). This decision is deliberately a non-change to those two checks, proven rather than
  asserted.

**Verified offline:**
- A human-entered value matching NO declared input (a "Remarks" field, `"Thanks for your
  business"`) is reported in `report["constants"]`, exactly as an agent-typed constant would be
  (`OFFLINE 12d`).
- A human-entered value that DOES match a declared input (`payee_name`, `"Nagarjuana"`), where the
  capability spec's own `description` text also happens to contain that literal un-parameterized,
  still triggers `find_leftovers`' refusal, naming the input and the location (`"description"`),
  never the value (`OFFLINE 12e`) -- proving the human-entered path was not special-cased to skip
  this check.
- The full bill-pay-shaped fixture (`OFFLINE 12c`) shows both synthesized steps (`type`, `select`)
  present in `task.steps` with `why == HUMAN_ENTRY_WHY`, alongside the agent's own un-annotated
  steps (`why: None`) -- the note is additive, not something every step now carries.

**Brief ref:** 3.2 (reviewability), 3.4 (parameterisation and the leftover check), D29, D44, D49.

> **Update: corrected, see D90.** The first bullet above -- "a human-entered value matching NO
> declared input is reported in `report["constants"]`, exactly as an agent-typed constant would
> be" -- was itself the bug found in the real `pay_bill.yaml` artifact: a value a human had to type
> in live, because the agent had no way to know it, was being permanently baked into the compiled
> capability as a frozen literal (`'3'`, `'4'`, `'34'`, `'4'`, `'4'` for Address/City/State/Zip
> Code/Phone #, every future replay silently submitting those same throwaway discovery values
> forever). D90 auto-declares a new input instead, for exactly this one case; an AGENT's own
> unmatched literal is completely unaffected and still becomes a reported constant, unchanged. The
> `OFFLINE 12d` fixture cited above was updated in place to assert the corrected behavior; see D90.

## R. Phase 4 bugfix: escalate's return value gates the risky click, not a side effect inside it

(Note on numbering: D82-D84 were taken by concurrent Phase 3 work landed in this same repo while
this fix was being written; this section continues from D84, the current highest number,
confirmed against `git log`/`grep "^### D"` immediately before writing it, not against an earlier
read.)

### D85 — `escalate`'s return value, not a side effect inside it, decides whether a risky click happens

**Question:** `run_capability`/`run_capability_async`'s risky-click branch (D38, D79) called
`escalate(reason, ctx)` and then unconditionally returned `NEEDS_APPROVAL`, ignoring whatever
`escalate` returned. `notebooks/05_replay_live.py`'s `make_escalate` worked around this by having
`escalate` itself resolve the target and call `surface.click(ref)` as a side effect on Approve --
but the engine still always returned `NEEDS_APPROVAL` afterward, so a real payment could go
through with no way to tell, from the typed `ReplayResult`, whether it had (Approve) or had not
(Reject) -- both left `status == "NEEDS_APPROVAL"`, byte-identical. Worse, the capability's own
remaining steps -- an `extract` reading the real confirmation, the final `checkpoint` -- were never
reached even on a genuine Approve, because the engine returned before them regardless. How should
approving a risky click actually take effect?

**Options:**
- (a) Keep `escalate` performing the click as a side effect (the status quo above). Rejected: it
  is not `escalate`'s job to act on the page -- every other step type's acting is the engine's job
  -- and it can never make the returned result honestly distinguish approved-and-paid from
  rejected-and-nothing-happened without inventing a fifth status (out of scope, D79 already named
  this as the real fix and deferred it).
- (b) Have `run_capability`/`run_capability_async` consult `escalate`'s return value: a specific
  sentinel means "proceed," anything else means "stay `NEEDS_APPROVAL`," exactly as today. The
  engine performs the click itself, via the exact same resolve-then-click code an ordinary click
  step already uses, and continues the loop into the capability's remaining steps.
- (c) Add a fifth `ReplayResult` status (e.g. `APPROVED_AND_CONTINUED`) so callers can tell
  Approve apart from Reject without changing what happens after either. Rejected as a bigger,
  separate schema/contract change than this task asked for (D27's four-status contract is
  load-bearing elsewhere); D79 already named this as a legitimate future direction, not this fix.

**Chosen:** (b). The contract: `escalate(reason, ctx)` may return the string `"approve"` to mean
"proceed with this click"; anything else (including `None`, the default for every existing fake
escalate in every offline test) means "no decision -- stay `NEEDS_APPROVAL`," the exact current
behavior. `escalate` itself must never perform the click any more -- that is the engine's job now,
like every other step type. On `"approve"`, the engine resolves the step's target (primary then
fallback, via the SAME `resolve_target`/`resolve_target_async` an ordinary click already calls --
not a second implementation) and calls `surface.click(ref)`, then lets the step loop continue past
it exactly as an under-the-limit risky click already does. If the target cannot be resolved even
after approval, the SAME `ResolutionError` handling an ordinary unresolvable target already goes
through applies unchanged, returning `FAILED` -- not a silent success, not `NEEDS_APPROVAL`. A
small pure helper, `_is_approved(decision) -> bool` (`decision == "approve"`), is shared by both
engines' risky-click branches, the same "factor out the shared pure decision, don't hand-copy it"
pattern D77 already used for `_target_locators`/`_find_outcome_rule` -- so the sync and async
engines can never disagree about what counts as approval.

**Reasoning:**
- This is the smallest change that actually closes D79's own honestly-stated gap: the returned
  `ReplayResult` now genuinely reflects what happened (an approved risky click that goes on to
  `SUCCESS` with the real confirmation and a verified checkpoint looks nothing like a rejected one
  that stays `NEEDS_APPROVAL`), without inventing a new status or touching the four-status
  contract (D27) at all.
- Reusing the existing resolve-then-click and `ResolutionError` paths, rather than writing a
  second one for "the approved case," is exactly the "reuse or closely mirror... do not invent a
  third way" principle this codebase already applies elsewhere (D22, D78); it also means the
  approved-but-unresolvable case gets `FAILED` for free, with no new code to get wrong.
- `_call_escalate` (D77's async helper) already existed to await `escalate`'s return value for a
  different reason (letting a real human finish deciding before the function returns); it now also
  returns that value instead of discarding it -- a strict widening, not a behavior change, since
  every existing caller of `_call_escalate` already ignored its (previously always-`None`) return.
- **Byte-for-byte compatibility, verified by running `uv run python notebooks/04_replay_engine.py`
  after the change:** every prior sync and async test's output line is unchanged, because every
  existing fake `escalate` (including every lambda that appends to a list and returns `None`
  implicitly) still produces a decision of `None`, which `_is_approved` still treats as "not
  approved" -- the exact same `NEEDS_APPROVAL` outcome as before this fix, for every prior test.
- `notebooks/05_replay_live.py`'s `make_escalate` was updated to match: it now only shows the
  decision bar and reports the human's choice (`"approve"` / `None` / `None` for Approve / Reject
  / Take-over respectively) and never touches the page itself for this branch -- only `make_escalate`
  and its surrounding markdown were touched, per this task's own scope limit; the file was never
  executed, only `ast.parse`d, per this repo's standing hard rule for that notebook.
- Take-over deliberately still returns a non-`"approve"` value (not `"approve"`): a human taking
  over the browser directly is a separate, already-handled path (D14, D79), and the engine cannot
  safely infer that the click happened just because control changed hands -- returning anything
  else here would be a new, unverified assumption, not something this fix's scope asked for.

**Cost, honestly stated:** `escalate` is called with the SAME reason string and step context
whether or not the step ends up approved; a caller reading only the `escalate` call count (rather
than its return value) still cannot tell approval from rejection -- this was never the signal to
read for that distinction, either before or after this fix; the `ReplayResult`'s own `status` is.
`_is_approved`'s equality check is intentionally exact-string (`"approve"`, not case-insensitive or
prefix-matched) -- easy to get wrong by hand if a caller does not read the contract; documented
here and in both engines' docstrings rather than guarded with fuzzy matching that could itself
approve something unintended.

**Update to D79:** the design D79 chose (escalate resolves and clicks as a side effect, engine
always returns `NEEDS_APPROVAL` regardless of the human's choice) is corrected by this decision.
See the "Update: corrected, see D85" note added directly to D79, above.

**Brief ref:** 3.3 (replay, no LLM in the loop, structured result), 3.4, 3.6, D20, D27, D28, D33,
D38, D77, D79.

## S. Phase 3 bugfix: a premature risky click survives compilation as a second point of no return

(Numbering confirmed against `git log`/`grep "^### D"` immediately before writing this, not from
memory: D85 is the current highest number. This section continues from D86.)

### D86 — A dead-end risky click is told apart from a real one by same-target-retried evidence, not by excluding risky clicks from dead-end detection

**Question:** a REAL captured discovery run against ParaBank (`artifacts/pay_bill.yaml`, a real $20
bill payment) compiled with TWO `risk: risky` "Send Payment" clicks, identical target, the FIRST
one sitting BEFORE the Address/City/State/Zip/Phone fields it needed -- a premature, failed
submission attempt that should never have survived compilation as a real step, let alone as a
second risky point-of-no-return. `compile_run`'s existing dead-end-removal rule (`drop_detours`,
D23/D43, proven by the `OFFLINE 8` fixture) did not catch it. Why not, exactly, and what is the
honest fix, given this artifact is about to be replayed for real with both risky clicks auto-firing
under a sane `auto_approve_limit` (worst case: an actual duplicate payment)?

**Root cause, confirmed by tracing the actual code against a reconstructed fixture (`OFFLINE 13g`,
built because no raw event log survived this real run -- `SCRATCH` is git-ignored and this run's
own events were never persisted), not guessed:**
- `drop_detours` only recognizes ONE dead-end shape: a NAV_TOOL click whose URL changes, followed
  by a later NAV_TOOL click whose `after` URL returns to the FIRST click's `before` URL, with only
  OTHER NAV_TOOL events in between (its inner loop `break`s the instant it sees anything else). A
  premature Bill Pay submission is a different shape entirely: ParaBank's own validation-failure
  response redisplays `billpay.htm` with the exact SAME url and heading (nothing ever "left"), so
  the outer condition (`e["after"]["url"] != e["before"]["url"]`) is false and the click is never
  even considered a candidate. And the fields a human fills in to actually succeed
  (Address/City/State/Zip/Phone, D82/D83's `synthesize_human_entries`) are `type_text` events
  sitting BETWEEN the two clicks -- which breaks the inner loop's adjacency requirement regardless.
  **Neither of the two hypotheses checked first was, alone, the real cause:** it is not a
  byte-identical URL/heading MISMATCH (`drop_detours` never inspects heading at all, anywhere), and
  it is not solely the blanket `not e.get("approved")` exclusion that DID also exist on both sides
  of the check (confirmed real, and removed by this fix, below) -- verified directly by patching
  ONLY that exclusion out and re-running the reconstructed fixture against the unfixed algorithm:
  the bug reproduced identically (still 2 risky clicks), because the intervening `type_text` events
  break the loop's adjacency before "approved" is ever consulted. The real cause is structural:
  `drop_detours`'s whole model is "wrong navigation, then correction," and a same-page failed
  resubmission with real typing in between is a shape it was never built to see.

**Chosen:** two changes, both to `notebooks/03_recorder.py`'s `OFFLINE 4` cell:
1. **Remove the blanket `not e.get("approved")` / `k.get("approved")` exclusion from `drop_detours`
   itself.** A risky click is now eligible for that exact existing check, same as any other click --
   it is no longer assumed safe-by-default just because it is risky. (Verified non-breaking: this
   exclusion was never load-bearing for any of the 25 pre-existing OFFLINE fixtures -- every risky
   click in them keeps its own url unchanged before/after, so the check's outer condition was
   always false for them regardless of the exclusion.)
2. **Add a new, separate function, `drop_dead_end_risky_clicks`,** for the shape `drop_detours`
   cannot represent. Signal used (the task's own first-preference signal): the SAME click target
   (`_key(e)`: tool, role, name, tag, container role, nth, value, label, path) appears more than
   once among a run's risky clicks. A click on that target whose own before/after state (url AND
   heading, both) is byte-identical -- it plainly achieved nothing -- is a dead end, PROVIDED it is
   not the LAST click on that target (there must be a later one that could be the genuine
   point of no return; a lone no-op risky click with no retry is left untouched, since there is no
   real evidence either way). A risky click whose state DID change is NEVER touched, however
   similar a later click on the same target looks. **If more than one click on the same target
   shows a real state change, `compile_run` refuses outright, naming both events** -- there is no
   honest way to tell which (if either) is the genuine point of no return without guessing, and
   this codebase never silently guesses at money-moving evidence (D82's own standing principle).
   `compile_run` calls this right after `drop_detours`, before `split_login`.

**Reasoning:**
- This directly matches the task's own preferred signal ("the same target is clicked again later
  in the same run with no successful outcome/checkpoint match in between") rather than trying to
  force-fit the unrelated byte-identical-URL/heading idea, which does not describe any code that
  actually exists in `drop_detours`.
- Removing the blanket `approved` exclusion (item 1) is the correct, principled reading of "a risky
  click is eligible for the existing dead-end-removal check same as any other click" even though,
  confirmed above, it is not BY ITSELF sufficient to explain this bug -- leaving it in place would
  still be an unprincipled "assume risky implies safe-to-keep" shortcut for the shape `drop_detours`
  CAN represent (e.g. a risky click that genuinely navigates to a distinct confirmation URL,
  followed by a separate later click that returns to the original page with nothing typed in
  between -- `drop_detours`'s own existing shape, just never applied to risky clicks before).
- The three acceptable-outcome fixtures the task named are each proven directly, not assumed:
  (a) a genuinely dead-end risky click (no state change, same target retried later) is removed,
  exactly as a dead-end safe click already is (`OFFLINE 13d`, fixture 13a);
  (b) a risky click that DOES change state is never touched, even next to a later click on the same
  target that also looks like a no-op (`OFFLINE 13e`, fixture 13b);
  (c) two risky clicks on the same target that BOTH show a real state change refuse loudly, naming
  both event numbers, rather than silently picking one (`OFFLINE 13f`, fixture 13c).
- The reconstructed real bug (`OFFLINE 13g`, fixture 14) -- built from the real artifact's own
  steps since no raw event log survived, per this task's instructions -- reproduces the exact
  double-risky-click shape against the UNFIXED `compile_run`, and produces exactly ONE risky "Send
  Payment" click, positioned after all 9 fields (payee name, account, verify account, amount,
  address, city, state, zip, phone), against the FIXED one.
- `artifacts/pay_bill.yaml` was regenerated for real from this fixture's actual `Capability` object
  (via `save_capability`/`to_yaml`), not hand-edited -- the file on disk is genuinely what the fixed
  compiler produces.

**Cost, honestly stated:** the "no-op, not the last click" signal only fires when there IS a later
click on the identical target -- a single dead-end risky click with no retry at all is left alone
(no structural evidence either way, and D82's own principle says never guess). The ambiguous-refusal
case (item (c)) means a run with two genuinely distinct real risky actions on the identical-looking
target (a legitimate two-step confirmation flow, for instance) will refuse to compile at all until
a human reviews it by hand; this is a deliberate, stated trade-off (fail loudly over guessing
wrong), not an oversight.

**Brief ref:** 3.2, 3.4 (risky action handling), Section 9 (real-money safety), D23, D43, D49, D82.

## T. Phase 4 live bugfix: `get_account_balance` failed to resolve `extract` against the real ParaBank Accounts Overview page

(Numbering confirmed against `git log`/`grep "^### D"` immediately before writing this, not from
memory: D86 is the current highest number. This section continues from D87.)

A real, live run of `artifacts/get_account_balance.yaml` (the real recorder-captured artifact,
top-level `artifacts/`, not `artifacts/examples/`) through `05_replay_live.py`'s `replay_live`
against the real ParaBank site logged in successfully, navigated to `/overview.htm` successfully,
then failed at its one `extract` step: `neither primary nor fallback resolved`. The main session
dumped the real live DOM. Three separate real problems were found in it; D87-D89 below fix each.

### D87 — `bare()`'s trailing-decoration strip: one non-alphanumeric character, not just a colon

**Question:** `READ_LABELED_JS`'s `bare()` (`03_recorder.py` BROWSER 8; an identical copy lives in
`05_replay_live.py` Setup 7, D78) normalized a label for exact-match comparison by stripping only a
trailing colon (`s.replace(/:$/, '')`) before lowercasing. The real ParaBank Accounts Overview
table's column header is exactly `"Balance*"` (a footnote asterisk pointing at "*Balance includes
deposits that may be subject to holds"), confirmed from the real captured DOM, not guessed. The
declared locator says `label: Balance` (no asterisk). `bare("Balance") !== bare("Balance*")`, so
the exact-match `hits` filter never found it, and `resolve()` correctly, but unhelpfully, reported
`None`.

**Chosen:** generalize the stripped character class from `/:$/` to `/[^a-zA-Z0-9]$/` -- ONE
trailing character, stripped only when it is not a letter or digit, applied identically to both the
wanted label and every candidate element's text (same as the old colon rule already did). This is a
strict superset of the old rule (a colon is itself non-alphanumeric, so every case the old regex
already handled is unchanged) and needed no change anywhere else in `READ_LABELED_JS` (the `hits`/
`valueOf` logic is untouched).

**Reasoning:** the task's own instruction was "at minimum `*`, and reasonably any single trailing
non-alphanumeric decoration character" -- a footnote asterisk today, a dagger/section-mark/hash
tomorrow on some other page, all the same shape (one trailing punctuation glyph, not part of the
label's actual words). Narrowly scoped on purpose: only the LAST character of an already
whitespace-normalized string, and only if it is not alphanumeric, so two labels that are genuinely
different anywhere in their actual text (e.g. `"Balance"` vs `"Available Amount"`) can never be
conflated by this change -- proven directly (see below), not assumed.

**Verification performed (offline proxy only, no browser -- stated plainly, not overclaimed as a
live check):** `bare()` runs inside `page.evaluate`, so it cannot be exercised directly without a
real page, which this task's hard rules forbid. JS and Python regex behave identically for this
simple case (a `$`-anchored single-character-class match on an already-normalized plain string, no
lookaround, no unicode edge cases), so a pure-Python mirror is a faithful proxy. Added as a new
`OFFLINE` cell in `03_recorder.py`, right after `BROWSER 8`:
```python
assert _bare_proxy("Balance") == _bare_proxy("Balance*") == "balance"       # the real bug, fixed
assert _bare_proxy("Balance") != _bare_proxy("Available Amount")            # not overloosened
assert _bare_proxy("Name:") == _bare_proxy("Name") == "name"                # old colon rule intact
```
All three pass (`uv run python -c "..."`, output: `balance balance available amount name`).

**Where fixed:** `03_recorder.py`'s `READ_LABELED_JS` is the origin (D78) and is the only place this
task's own instructions named for the code change. `05_replay_live.py`'s copy of the same string
(Setup 7) was ALSO updated, identically, because that copy is what the real bug actually runs
through, and the file's own comment already declares it must be "copied verbatim" from the
recorder's -- leaving it unfixed there would leave the live bug unfixed. Both copies are now
byte-identical again.

**Cost, honestly stated:** a label ending in a meaningful (non-decorative) trailing punctuation
mark, e.g. a genuine question `"Are you sure?"`, would now bare-match `"Are you sure"` too -- the
same category of intentional looseness the pre-existing colon rule already accepted (`"Name:"` /
`"Name"`), just widened by one character class. No case in either bundled example artifact is
affected either way.

**Brief ref:** 3.2 (locator robustness), D46, D68, D78.

### D88 — `PlaywrightReplaySurface.resolve()` gets a bounded poll/retry for asynchronously-loaded page content

**Question:** ParaBank's real `/overview.htm` renders its account table's `<tbody>` empty at
initial page load, then fills it via a separate jQuery `$.ajax` call that runs inside
`$(document).ready`, AFTER the page's own `load` event (confirmed from the real page's own
`<script>`, not guessed). `05_replay_live.py`'s `navigate()` only awaits `page.goto`, and
`resolve()` made exactly one immediate attempt before reporting a miss -- a correct label match
could still race that AJAX call on a slow network or server, independent of D87's fix.

**Chosen:** a bounded poll loop added INSIDE `PlaywrightReplaySurface.resolve()` only. The prior
single-attempt logic was factored, unchanged, into a new private `_resolve_once(locator)`; `resolve()`
now calls it in a `while True` loop: return immediately on a hit, otherwise sleep
`_RESOLVE_POLL_INTERVAL_S` (0.4s) and retry, until a wall-clock deadline `_RESOLVE_POLL_BUDGET_S`
(5.0s total, measured from `resolve()`'s own start, via `asyncio.get_event_loop().time()`) is
reached, at which point it returns `None` -- today's behavior, unchanged, once the budget is spent.
Applied to BOTH branches inside `_resolve_once` (the direct `labeled_value` READ_LABELED_JS path
AND the general numbered-scan-then-DESCRIBE_JS path) -- judged equally exposed: any page's
interactive controls, not only a `labeled_value` target, could just as easily be inserted by a
late-running script, and the poll itself is cheap and self-contained either way.

**Reasoning:** kept deliberately narrow, per the task's own instruction -- no new dependency, no
generic wait-for-selector abstraction, no change to `04_replay_engine.py`'s already-tested
`TransientFailure`/retry contract (D26, a different mechanism: that one retries a whole STEP after
a raised exception; this one is `resolve()` re-checking the live DOM a few times before ever
reporting a miss to its caller at all), and no change to `AsyncReplaySurface`'s interface
(`resolve(locator) -> ref | None` is unchanged; only what happens INSIDE the real implementation
changed). 5 seconds matches this codebase's existing bounded-retry philosophy (D26's own bounded
`max_retries`, not unbounded polling).

**Cost, honestly stated:** a resolution that is a TRUE miss (the target genuinely does not exist)
now takes up to 5 seconds longer to report `FAILED`/fall through to the fallback locator, instead of
failing instantly -- a deliberate trade against the alternative of a real page's async content
being mistaken for a true miss. Not exercised live here (this task's hard rules forbid running a
real browser); the main session should confirm the actual wait was short (well under 5s) on the
real page, not that it silently used the whole budget every time.

**Brief ref:** 3.2, 3.7 (heterogeneous surfaces), D26, D78.

### D89 — `get_account_balance.yaml`'s `extract` step targeted the wrong thing regardless of account count; repointed at the page's own "Total" row

**Question:** even with D87+D88 both fixed, is a `labeled_value` extract of `"Balance"`/`"Balance*"`
on `/overview.htm` actually correct? The real table's structure (confirmed from the real captured
DOM):
```
<table id="accountTable">
  <thead><tr><th>Account</th><th>Balance*</th><th>Available Amount</th></tr></thead>
  <tbody> <!-- filled async: one <tr> per account, columns id / balance / available amount --> </tbody>
  <tfoot><tr><td colspan="3">*Balance includes deposits...</td></tr></tfoot>
</table>
```
`READ_LABELED_JS`'s `valueOf()` reads "the cell after" the matched element. The ONLY element on
this page whose bare text equals `"balance"` is the `<th>Balance*</th>` HEADER cell itself -- no
`<tbody>` data cell ever contains the literal text "Balance" (data rows hold an id, a formatted
amount, and another formatted amount, nothing labeled). So `valueOf()` on that header's own next
sibling returns the string `"Available Amount"` -- a second COLUMN HEADER, not any account's
balance figure -- for a test user with 1 account, 2 accounts, or 20. This is NOT the ambiguity the
task first hypothesized ("which of several rows"); it is a flat structural mismatch that would
happen even for a single-account user, because the only textual anchor matching "Balance" at all is
the header row, never a data row. (Confirmed by reasoning about `READ_LABELED_JS`'s own code against
the real DOM given -- not by running a real page, forbidden here by this task's hard rules.)

**Both branches the task asked to weigh, resolved by this one finding:**
- (a) "Problems 1+2 alone are sufficient, if the real account has exactly one row" -- FALSE,
  independent of row count, for the reason above: the match happens on the header row, not any data
  row, no matter how many data rows exist.
- (b) "the capability needs a different, more specific locator" -- TRUE, but not for the
  account-count reason originally suspected; for the header-vs-data-row reason confirmed above.

**Why a true per-`account_id` fix (mirroring `examples/get_account_balance.yaml`'s
`activity.htm?id={{account_id}}` approach) is not reachable here without an out-of-scope change:**
that example page is parameterized through `navigate`'s `path`, which the engine already runs
through `render()` (`04_replay_engine.py` Section 3/8) to substitute `{{input}}`. A row-specific
match on `/overview.htm` would need the SAME kind of substitution inside a locator's `label` field
(e.g. `label: '{{account_id}}'`, matching the account-id `<td>` in a specific row, then reading its
own next sibling for that row's balance -- mechanically sound, using the existing `labeled_value`
JS unchanged) -- but `render()` is only ever called on `step.path`/`step.value`/`step.option`
(confirmed by reading every call site in `04_replay_engine.py`), never on a locator field, for any
strategy. Adding that would mean changing `04_replay_engine.py`, explicitly forbidden by this task.
A `structure`/`text` locator aimed at a specific `<td>` is equally unreachable today for an
unrelated reason: `OBSERVE_JS` (`05_replay_live.py` Setup 4, copied verbatim from `agent.ipynb`)
only numbers INTERACTIVE elements (`a[href], button, input, select, textarea, [role=button],
[role=link], [onclick]`) -- a plain `<td>` holding a currency amount is never assigned a
`data-cua-ref` at all, so `resolve()`'s general numbered-scan branch would never even see it as a
candidate (the same gap D78 already documented for a `text`-strategy confirmation heading on
`transfer_funds`, just hit here by a different capability). Widening `OBSERVE_JS`'s selector was
judged out of scope: it is shared, verbatim-copied production scanning logic this task did not ask
to touch, with unclear ripple effects on every other call site that assumes it only numbers
clickable/fillable things.

**Chosen:** hand-edit `artifacts/get_account_balance.yaml` (real code path, `compile_run`, was not
run here -- see below for why) to repoint the SAME `labeled_value` locator at the table's own footer
row, `label: Total`, appended by the identical async call that fills `<tbody>`, which sums every
account's balance (`formatCurrency(totalBalance)`). `<b>Total</b>`'s next sibling `<td>` is exactly
the total figure -- this uses the existing, unmodified `labeled_value`/`READ_LABELED_JS` mechanism,
no schema or engine change, and resolves to a real, correct number today. The capability's top-level
`description` and its one output's `description` were also corrected: both previously implied a
per-`account_id` scoping (`"given its account id"`, a literal, never-substituted `{{account_id}}`
in the output description) that no declared input ever backed (`inputs: []` already, both before
and after this change) -- now they accurately say "total balance across all accounts."

**Why hand-edited, not regenerated via `compile_run`:** this task's own hard rules reserve the rest
of `03_recorder.py`'s recorder/compile logic for a separate, concurrent task; running `compile_run`
end to end here (which would need a live capture run to compile from, at minimum) risks exactly the
conflict those rules warn against. The file was edited directly and validated OFFLINE by loading it
through the real, unmodified `Capability`/`from_yaml` (`02_artifact_schema.py`, executed read-only
in an isolated namespace, no browser): it loads without error, `outputs`, `steps`, and `checkpoint`
all round-trip as expected.

**Cost, honestly stated -- what the live main session must still check:** "Total" is numerically
identical to "the balance" only when the real test user has exactly one account; for a user with
more than one, it is the CORRECT SUM across all of them (a real, honest, unambiguous answer to "the
balance shown on this page"), not any one specific account's figure -- if the take-home's real
grading expects one specific account's number instead of the total, this capability's declared
scope should be renegotiated with a real schema/engine change (out of scope here), not silently
guessed at. This was not verifiable from static evidence alone; flagged rather than assumed.

**Brief ref:** 3.2 (locator robustness), D46, D63, D68, D78, D87, D88.

## U. Phase 3 bugfix: a human-entered value matching no declared input is auto-promoted to a new input, never baked in as a literal

(Numbering confirmed against `git log`/`grep "^### D"` immediately before writing this: D89 is the
current highest number. This section continues from D90.)

### D90 — An unmatched human-entered value is auto-declared as a new input, named from its field's label, never kept as a literal

**Question:** the real `artifacts/pay_bill.yaml` (a real recorder capture run, already fixed once
for D86) compiled with five `type` steps carrying hardcoded literal values (`'3'`, `'4'`, `'34'`,
`'4'`, `'4'`, for Address/City/State/Zip Code/Phone #) -- values a human had to type in live, during
a `request_missing_values` handoff, because ParaBank required them and the agent never had them
(D82/D83's `synthesize_human_entries`). Every future replay of `pay_bill` would silently submit
those same throwaway discovery values forever, with no way for a caller to supply the payee's real
address, city, state, zip, or phone. `build_steps`/`_params` (D8/D9/D10/D29/D33/D38/D44) already had
a rule for "a typed value matches no declared input": keep it as a literal and report it in
`report["constants"]` for a reviewer to see. That rule is correct for an AGENT's own unmatched
literal (nobody asked for it to be variable; flagging it is enough). It is exactly backwards for a
HUMAN-entered one: the agent had no way to know this value, which is the one category of value that
should always require a real one from the caller on every future run.

**Options:**
- (a) Leave the existing rule alone and rely on a reviewer noticing the constant and manually
  promoting it to a declared input before verifying the capability. Rejected: this is precisely what
  happened in the real bug report -- the constant WAS reported, and it was still shipped as
  `artifacts/pay_bill.yaml` with the literals baked in. A rule that depends on a human catching its
  own honestly-reported warning, every time, is not a fix.
- (b) Auto-declare a new input for exactly this one case (human-entered, matches nothing declared),
  named from the field's own label, and substitute `{{that_name}}` for the step's value. An agent's
  own unmatched literal is completely untouched by this -- still kept and reported as a constant,
  exactly as before.

**Chosen:** (b), implemented in `notebooks/03_recorder.py`'s `OFFLINE 5` cell (`_params`,
`_declare_human_input`, `_slugify_label`, and `build_steps`'s call sites), plus a defensive change to
`compile_run` (below).

**Design, one decision at a time:**

1. **Name derivation (`_slugify_label`):** the field's own label -- the same text already used for
   that field's `label` locator strategy (e.g. `'Address:'`, `'Zip Code:'`, `'Phone #:'`) -- is
   lowercased, runs of non-alphanumeric characters collapsed to one underscore, and leading/trailing
   underscores stripped: `'Address:'` -> `address`, `'Zip Code:'` -> `zip_code`, `'Phone #:'` ->
   `phone`. Never derived from the field's VALUE -- see point 2 below for why that distinction is
   load-bearing, not stylistic. A field with no usable label at all (D67's known gap -- the slug
   comes out empty) refuses compilation, naming the event, rather than inventing an opaque name for
   something with no real signal.
2. **Naming by label, not by value, and never re-matching a newly auto-declared input by value:**
   the real bug report has THREE separate human-entered fields (City, Zip Code, Phone #) that all
   happen to carry the identical throwaway discovery value `'4'` (`same_value`'s own numeric
   canonicalization makes `'4' == '4'` trivially true). If a newly auto-declared input were added
   back into the `inputs` name->value map `_params` matches against, City's `'4'` would auto-declare
   `city`, and then Zip's `'4'` would then WRONGLY match `city` by value (same bug this decision
   exists to prevent, just moved one field over) -- and Phone's `'4'` would match it too. The fix:
   `_params`'s value-matching loop (`same_value`/`substitute`) only ever consults `inputs`, a
   snapshot taken ONCE at the top of `build_steps`, from the specs the CALLER originally declared.
   An input this function itself auto-declares is written into `specs` (read again by `_cap` after
   `build_steps` returns, so it reaches `Capability.inputs` and the leftover check) but deliberately
   NEVER back into `inputs` -- so every human-entered field is named, and only named, from its own
   label, regardless of what any other field's value happens to be.
3. **Type and pattern:** a generic `type: string` with pattern `^.{1,80}$` -- wide enough not to
   reject a real value the recorder never saw an example of, bounded only to stop something absurd
   (matching the style of this schema's other free-text inputs, e.g. `payee_name`'s `^.{2,80}$`).
   Deliberately NOT a stricter guess (e.g. 5-digit zip, digits-only phone): the recorder saw exactly
   ONE throwaway example per field (`'4'`, a single character) and has no basis to infer a real
   value's shape. A stricter pattern invented from a single unrepresentative discovery sample risks
   rejecting a real, valid value on the very first real run -- worse than accepting a too-wide one.
4. **Description:** built from the label, e.g. `"Address:"` -> `"Address, entered by a human during
   discovery -- provide the real value for each run."` -- matching this file's existing style for an
   auto/derived description (compare `build_steps`'s own default extract-output description, `f"The
   value shown next to '{e['label']}'."`).
5. **Collision handling:** two different labels producing the same slug, or a slug that matches an
   ALREADY-declared input's name (from the original spec, or an earlier auto-declare in the same
   run), is disambiguated with a deterministic `_2`, `_3`, ... suffix, checked and reserved via a
   `used_names` set BEFORE `specs` is touched -- never a silent overwrite of one input's own
   declaration with another's.
6. **The step's `why` note:** unchanged from D84 (`HUMAN_ENTRY_WHY`) -- a human-entered step already
   carries a reviewer-facing note; this decision does not need a second one saying "and it's now an
   input" as well, since the compiled YAML's own `inputs:` list already shows that plainly.
7. **Order of declared inputs:** `specs` is a plain dict, mutated in place by appending new entries
   as their events are processed, in run order -- Python dicts preserve insertion order, so the
   compiled `Capability.inputs` list is deterministically: every originally-declared input (in the
   caller's own order), then every auto-declared one, in the order its event occurred in the run. No
   extra bookkeeping needed for this.
8. **`compile_run` copies `spec["inputs"]` before compiling (defensive, found while implementing
   this):** `specs` is now mutated during `build_steps`. Left as the caller's own dict object, this
   would leak newly auto-declared inputs back into a `spec` object the caller might reuse across more
   than one `compile_run` call -- exactly what several `OFFLINE` fixtures below deliberately do
   (`BILLPAY_SPEC` is compiled against more than once). `compile_run` now does `specs =
   dict(spec["inputs"])` (a shallow copy -- the inner per-input dicts are never mutated, only new
   keys added, so a shallow copy is sufficient) before any auto-declare can happen, so each
   `compile_run` call's auto-declared inputs stay local to that call, proven directly (`OFFLINE 12d`'s
   own fixture asserts `BILLPAY_SPEC["inputs"]` is untouched after a call that auto-declares
   `remarks`).

**This must NOT, and does NOT, change how an agent's own unmatched literal is handled:** `_params`
only takes the auto-declare branch when `human_entered` is true; without it, the exact prior
behavior runs unchanged (kept as a literal, appended to `constants`). Proven by `OFFLINE 13i` (new):
an ordinary agent `type_text` into an unmatched field is still a plain literal constant, `why: None`,
no input created for it -- byte-identical to what this exact scenario would have produced before
this decision.

**D84 is corrected, not just extended:** D84 asserted the OLD behavior for exactly this sub-case
("a human-entered value matching no declared input is reported in `report["constants"]`, exactly as
an agent-typed constant would be") as its own verified claim -- that claim was the bug. See the
"Update: corrected, see D90" note added directly to D84, above. `OFFLINE 12d`'s fixture (D84's own)
was updated in place to assert the corrected behavior, not left asserting the superseded one.

**Verified offline (all in `notebooks/03_recorder.py`):**
- `OFFLINE 12d` (updated): a human-entered "Remarks" value matching no declared input is now
  auto-declared as input `remarks` (type `string`, pattern `^.{1,80}$`, the exact description text
  above), the step's value becomes `{{remarks}}`, and `report["constants"]` is empty -- also proves
  `compile_run` never mutates the caller's own `spec["inputs"]` dict (point 8 above).
- `OFFLINE 12c` (unchanged, re-confirmed): a human-entered value that DOES match an already-declared
  input (`payee_name`, `from_account`) still parameterizes to that existing input; `task.inputs`
  names are exactly `{"amount", "payee_name", "from_account"}` -- no duplicate, unaffected by this
  decision, exactly as it worked before it.
- `OFFLINE 13h` (new): two human-entered fields sharing the label `"Note:"` disambiguate to `note`/
  `note_2`; a third, labeled `"Amount:"` with a value that does NOT match the already-declared
  `amount` input, disambiguates to `amount_2` -- and the ORIGINAL `amount` input's own declaration
  (`type: currency`, `description: "Amount to pay."`) is confirmed untouched.
- `OFFLINE 13i` (new): an ordinary agent-typed literal matching no input is still a plain literal
  constant, `why: None`, never auto-declared -- the regression fixture for the "must not change"
  requirement above.
- The reconstructed real bug report (`OFFLINE 13g`, extended): all 5 human-entered fields
  (Address/City/State/Zip Code/Phone #) -- three of which (City, Zip, Phone) share the identical
  throwaway value `'4'` -- each become their OWN declared input (`address`, `city`, `state`,
  `zip_code`, `phone`), no raw literal survives anywhere in the compiled capability, and
  `report["constants"]` is empty.
- The full `OFFLINE`-cell suite (32 cells as of this decision) re-run top to bottom: every
  pre-existing fixture (including D82-D86's) still passes, unchanged, alongside the new ones.

**`artifacts/pay_bill.yaml` regenerated for real** (never hand-edited) by running the reconstructed
`OFFLINE 13g` fixture through the fixed `compile_run`, then `save_capability` on its actual output --
the same procedure D86 used for its own regeneration of this file. Its `inputs:` list now has
`payee_name`, `payee_account`, `amount` (unchanged) plus the five new `address`, `city`, `state`,
`zip_code`, `phone` inputs; its five human-entered `type` steps now read `{{address}}`, `{{city}}`,
`{{state}}`, `{{zip_code}}`, `{{phone}}` in place of the literals `'3'`, `'4'`, `'34'`, `'4'`, `'4'`.
Every other line (locators, the other 4 steps, checkpoint, `outcome_rules`) is byte-identical to the
version D86 produced.

**Cost, honestly stated:** the pattern (`^.{1,80}$`) is deliberately as weak as this schema's own
generic string inputs get -- it will accept a real value that would fail a stricter, hand-written
pattern a reviewer might later want (e.g. a real zip-code format check), and this decision does not
attempt to guess one from a single discovery sample. A `draft` capability with auto-declared inputs
still needs a human reviewer to read their descriptions and decide whether a stricter pattern is
worth hand-adding before promoting the capability to `verified` -- this decision makes the VALUES
safe (never frozen), not the validation strict; tightening validation remains an explicit, separate,
reviewed choice, never guessed by the compiler. Two human-entered fields that are genuinely the same
real-world value (e.g. a payee's account number typed twice, once to confirm) will still get two
separate auto-declared inputs if neither matches an originally-declared input -- naming by label, not
value, deliberately never tries to deduplicate across fields by coincidental value equality (see
point 2); a caller supplying that capability's real values simply supplies the same value twice, at
no correctness cost, only a small readability one.

**Brief ref:** 3.2 (reviewability), 3.4 (safety, parameterisation, never silently accept an
unexplained literal), 3.6 (a well-reasoned mechanism, not a blanket one), D8, D9, D10, D29, D33, D38,
D44, D49, D82, D83, D84, D86.

## V. Phase 4 live bugfix: `replay_live()` gets a pre-flight gate for missing required inputs

### D91 — A pre-flight `input()` gate in `replay_live()` prompts for missing required inputs before anything starts; `validate_inputs`/`run_capability_async` are untouched

**Question:** the owner, running `notebooks/05_replay_live.py` live against `artifacts/pay_bill.yaml`
(D90 had already turned `address`/`city`/`state`/`zip_code`/`phone` from baked-in literals into real
required inputs), hit:
```
InputValidationError: missing required input 'address'; missing required input 'city'; ...
```
as a raw traceback from `run_capability_async`'s own `validate_inputs` (04_replay_engine.py Section
3) -- exactly correct behavior (D29: a missing required input must refuse, never silently proceed),
but with no chance to notice and fix it before the whole run dies. The owner's own words, verbatim,
are the spec for what replaces the traceback:

1. "for a replay, the replay has to automatically understand what all fields it will require based
   on the replay [i.e. from the capability YAML's own declared inputs -- this is already figured
   out, by the agent, at discovery/compile time]. What all fields are supposed to be entered? That
   should be prompted to the user if he has not entered it. Tell him to enter it, and only then will
   things proceed."
2. "this has to be a safe step, so before anything starts, based on the YAML, you should ask the
   user, 'You have not entered these fields. Please enter these fields.'"

**Options:**
- (a) Catch `InputValidationError` around the `run_capability_async` call and print a nicer message.
  Rejected: the browser/login/step loop has already started running by the time `validate_inputs`
  raises (it is `run_capability_async`'s own first line, Section 9) -- a human filling in the
  missing fields at that point cannot "restart" the run from where it left off; the owner's own
  wording ("before anything starts... only then will things proceed") asks for the check to happen
  BEFORE any of that, not for a prettier error after some of it already ran.
- (b) A genuinely new pre-flight gate in `replay_live()` itself: compute which of `cap.inputs` are
  required and missing from the caller's own `inputs` dict, and if any are, prompt for each one
  (via `input()`) and merge the answers in, all before `run_capability_async` is ever called.

**Chosen:** (b), added as three new functions in `notebooks/05_replay_live.py`'s new "Pre-flight
input gate" cell (`missing_required_inputs`, `_prompt_for_missing_input`, `gather_missing_inputs`),
called from `replay_live()` itself, right after `from_yaml` and before `run_capability_async`.

**Why this lives in `replay_live()` only, never in `04_replay_engine.py`:** `run_capability`/
`run_capability_async` are the shared engine used by every caller, live or otherwise -- a real
production/scheduled/API-triggered replay has no human present, and must keep failing fast and
loudly on a missing required input, exactly as today. `validate_inputs` and the whole existing test
suite around it (sync + async, 8 + 3 + integration each, Sections 3b/4b/9b/10) are untouched, byte-
identical: `run_capability_async` still calls the real `validate_inputs` as its own first line, so a
value that somehow slips past this gate's own check still gets the engine's full type/pattern
validation regardless. `replay_live()` is different: it is always driven by a person sitting at this
Jupyter kernel (CLAUDE.md: "the user runs it"), so unlike a scheduled job, there is somewhere to ask.
This gate is purely additive and opt-in-by-construction -- it only ever activates when something is
actually missing, so it cannot change behavior for a capability that already has every required
input supplied (an already-fully-specified `pay_bill` call) or one with no required inputs at all
(`get_account_balance.yaml`, `inputs: []`).

**Why a plain `input()`, not a browser handoff:** discovery's `ask_human`/`request_value`
(agent.ipynb STEP 3, D82) exist because the LLM agent has no other channel to a human except the
page it is already showing them. Replay has no LLM and no discovery-time agent loop -- the "human"
here is simply whoever typed `await replay_live(...)` into the cell below, already looking at this
notebook's own terminal-style output, not necessarily at the ParaBank page at that instant. A
blocking `input()` (which runs fine inside a Jupyter cell -- Jupyter's own kernel handles stdin for
exactly this case) is the plainest, most direct channel to that person. Building lock/decision-bar
machinery for this would repurpose a mechanism designed for a mid-run human takeover of the PAGE to
solve a pre-run problem of missing call arguments -- a needless, riskier detour (it would need a
`page`/`surface` to exist and a browser tab to already be open, neither of which this gate should
require: it must be checkable, and useful, even before Setup 2's browser launches, in principle).

**The bounded-retry choice (`_PREFLIGHT_MAX_ATTEMPTS = 5`):** matches this file's own established
style for a bounded loop (`PlaywrightReplaySurface.resolve()`'s D88 poll budget is also a small,
explicit constant, not "retry forever" or "retry once"). A human can mistype a value; one attempt is
too unforgiving for an interactive prompt, but an unbounded retry loop could hang a notebook cell
indefinitely on a genuinely malformed value (or a scripted/non-interactive `input_fn` that always
returns garbage). 5 gives real room for a typo without ever looping forever; exhausting it raises
`InputValidationError` (the same exception `validate_inputs` itself raises for a missing/invalid
input, reused rather than inventing a second failure type for what is, from the caller's outside
view, the identical class of problem) naming the exact field, so the failure is as clear as the
traceback this replaces was, minus the surprise.

**Reuses, never reimplements, `validate_inputs`'s own pattern check:** `_prompt_for_missing_input`
calls the exact same `re.fullmatch(param.pattern, value)` `validate_inputs`
(`04_replay_engine.py` Section 3, line `elif param.pattern and not re.fullmatch(param.pattern,
value):`) already uses -- not a second regex-checking implementation living in this file.

**Never touches secrets (D32):** `missing_required_inputs`/`gather_missing_inputs` only ever look at
`cap.inputs`; `cap.secrets` (names only, resolved via `resolve_secret`) is never read, never
prompted for, never affected by any part of this change. A secret's value must still come only from
`.env`, exactly as before.

**Ambiguity, decided explicitly:** does a caller-supplied input given as `""` (or whitespace-only)
count as "missing", the same as a name absent from the `inputs` dict entirely? **Yes, both count as
missing.** A caller who passes `address=""` has not, in any way that matters to a real ParaBank bill
payment, supplied a real address -- treating an empty string as "present" would let the gate silently
skip exactly the case D90 exists to prevent (a throwaway/blank value sailing through untouched).
`missing_required_inputs` therefore checks `value is None or not str(value).strip()`, not just
`param.name not in inputs`. (`validate_inputs` itself, unmodified per the scoping above, still only
checks `name not in raw_inputs` for "missing" -- an empty string it receives directly, bypassing this
gate, would still pass its own `required` check and only fail `matches_value_type`/`pattern` if the
type/pattern reject it; that is `04_replay_engine.py`'s own existing, unchanged behavior, not
something this gate alters.)

**Verified offline** (`notebooks/scratch/test_preflight_gate.py`, git-ignored, `uv run python
notebooks/scratch/test_preflight_gate.py`; see that file/the task report for the full output) against
the REAL committed `artifacts/pay_bill.yaml` (the bug report's own capability) and
`artifacts/get_account_balance.yaml` (`inputs: []`):
- Several required inputs, some supplied, some not (including a gap-in-the-middle case) -> exactly
  the missing ones are identified, in `cap.inputs`' own declared order.
- A whitespace-only supplied value is treated as missing, same as an absent key.
- All inputs already supplied, and the `inputs: []` capability -> nothing flagged, and
  `gather_missing_inputs` never calls `input_fn` even once (true no-op), returns a NEW dict equal to,
  but not identical to, the caller's own.
- A monkeypatched `input()` feeding one bad-pattern answer then a good one -> rejected, retried,
  accepted, in exactly 2 calls.
- A monkeypatched `input()` feeding all-bad answers -> `InputValidationError` naming the exact field,
  after exactly `max_attempts` (5) calls, never more.
`input()` itself and the full `replay_live()` wiring were exercised only through this monkeypatched,
offline harness -- never a live Jupyter session; the main session performs the live check.

**Brief ref:** 3.2 (reviewability/usability of a safety refusal), 3.4 (safe, never silently proceed
without a real value), D26, D29, D32, D88, D90.

## W. Phase 8: evidence capture

### D92 — `evidence/`'s layout, and two small, additive capture helpers instead of changing the existing notebooks

**Question:** Phase 8 (roadmap row 8, citing D13/D24/D30) needs `evidence/` to actually hold
artifacts and logs for a discovery run and a replay run (Section 6's own deliverable, `DECISIONS.md`
line 35), across both flows and all five error cases (D30). D24 sketched a layout
(`log.jsonl`/`screenshots/`/`snapshot_step<N>.json`) before the Phase 3/4 rebuild existed; the actual
shapes now on hand are more concrete and better suited to what's already produced: 03_recorder.py
CAPTURE's own `events` list and `compile_run`'s `{"login", "task", "report"}`, and
05_replay_live.py's own `Capability`/inputs/`ReplayResult`. How should the folder be laid out, and
how should real runs get into it, given the hard rule that no agent may ever open a browser or touch
ParaBank?

**Options:**
- (a) Reconstruct D24's original `log.jsonl`/screenshot layout from scratch, ignoring what the
  current code actually produces.
- (b) A layout shaped directly around the current `events`/`Capability`/`report`/`ReplayResult`
  objects, written by two small, additive, offline-tested helper functions; nothing existing changed.
- (c) Fold evidence-saving directly into `03_recorder.py`'s COMPILE cells and `05_replay_live.py`'s
  `replay_live`, rewriting their own signatures/behavior.

**Chosen:** (b).

```
evidence/
  README.md
  discovery/<run-name>/
    goal.txt  events.json  capability.yaml  login_capability.yaml*  compile_report.json  transcript.log
  replay/<capability-name>-<case>/
    capability.yaml  inputs.json  result.json  transcript.log
```
(`*` only when a login capability was also compiled.) `<case>` is `success` or `error-<name>` for
one of the five cases below. Two new functions, `notebooks/evidence_capture.py` (new file, pure
Python, no browser import at all):
- `save_discovery_evidence(name, goal, events, capability, report, transcript_lines, evidence_dir=EVIDENCE_DISCOVERY_DIR, *, login=None, secret_values=())`
- `save_replay_evidence(cap, inputs, result, transcript_lines, evidence_dir=EVIDENCE_REPLAY_DIR, *, label=None, secret_values=())`

Both take objects a real run already has in hand and only ever write files -- neither runs a
discovery agent or a replay itself. `05_replay_live.py` gets one small, additive change: a new
`evidence_dir: pathlib.Path | None = None` parameter on `replay_live` (default `None` = today's
exact unchanged behavior, `logger=print`, nothing saved); when given, `logger` is teed into a
transcript list and `save_replay_evidence` is called once the result is known.
`run_capability_async`/`validate_inputs`/`compile_run`/`gather_missing_inputs` are not modified.

**Reasoning:**
- (a) would produce a layout disconnected from what the code actually emits, forcing an awkward
  translation step (or new instrumentation) at exactly the point the existing objects already carry
  everything needed. D24 was right about the goal (structured log + a richer failure signal); the
  concrete shape just moved on since D24 was written, before the Phase 3/4 rebuild existed.
- (c) would touch `compile_run`/`replay_live`, which this phase's own scoping rule forbids touching
  beyond one additive, opt-in parameter -- and it would make every existing offline test of those
  functions a place a future change could silently break evidence-saving too, for no benefit.
- (b) is the smallest change that satisfies the requirement: two pure functions, independently
  testable offline, that only add a new opt-in call site. A capability YAML saved into `evidence/` is
  always a fresh copy, never written back into `artifacts/*.yaml` -- `save_capability`'s own
  verified-overwrite guard is untouched and irrelevant here.

**Secret-value guard:** D32 requires a secret's value never be written anywhere, only its name. This
is already structural in this codebase's own data shapes -- a captured `type_secret` event's `value`
field is the secret's NAME (03_recorder.py `_capture`'s own `"type_secret": lambda kw: kw.get("name")`),
and a replay `inputs` dict never contains a secret at all (secrets are resolved separately via
`resolve_secret`). Both helpers additionally take an explicit, optional `secret_values` tuple and
refuse to write ANYTHING (matching `save_capability`'s own "refuse, never partially write" shape) if
any of those values is found in what's about to be written -- defense in depth against a future bug,
not a claim that one exists today.

**The five error demos (D30, cited by Phase 8, not reproposed here):** account not found (business
outcome), slow page (recoverable), session expired (recoverable), element missing (hard failure),
transfer over limit (`NEEDS_APPROVAL`). `evidence/README.md` writes these out as a numbered
checklist against the real, current capabilities (`artifacts/examples/get_account_balance.yaml` for
case 1, `artifacts/transfer_funds.yaml`/`pay_bill.yaml` for the others), with two honest caveats
recorded there rather than glossed over: (i) the live `PlaywrightReplaySurface.resolve()` (D88) has
its own silent poll/retry and never raises the `TransientFailure` the offline `FakeSurface` tests
exercise, so "slow page" demonstrates D88's live poll, not D26's `TransientFailure` path; (ii) a
`recoverable`/`relogin` outcome-rule match is, by `04_replay_engine.py`'s own documented comment,
only logged today, not actually acted on -- re-running the login capability and continuing is
explicit unbuilt Phase 9 scope -- so "session expired" is expected to end `FAILED` at the next step,
with the recoverable-match line in the transcript as the actual evidence of detection.

**Verified offline** (`uv run python notebooks/evidence_capture.py`; this agent's own run, since
this file imports nothing that touches a browser): fixtures built in the same style as
`03_recorder.py`'s own OFFLINE fixtures (a login + balance-read event list, a real example
`Capability` loaded read-only via `from_yaml`) and hand-built `ReplayResult`s for all four statuses
(`SUCCESS`/`BUSINESS_OUTCOME`/`NEEDS_APPROVAL`/`FAILED`) round-trip correctly through both helpers;
folder/file layout matches this design exactly; a `type_secret` event's `value` field is confirmed to
be the secret's NAME (`"username"`/`"password"`) and no fixture ever contains a real secret VALUE;
an adversarial fixture with a raw secret-like value injected, plus a matching `secret_values=(...)`,
is confirmed to raise `EvidenceWriteError` and write NOTHING (no folder at all) for both helpers. All
fixture output goes to a throwaway `tempfile.mkdtemp()` directory, never into the real `evidence/`
folder. `05_replay_live.py`'s edit was checked with `ast.parse` only -- never executed, per this
phase's hard rule (that file imports Playwright and needs a real browser + `.env`).

**Not done, deliberately, by this task:** any real discovery or replay run. `evidence/` is committed
with only `README.md` and two empty `discovery/`/`replay/` placeholder folders; `evidence/README.md`
carries the exact numbered checklist of live runs the project owner (or a future live session) still
needs to perform to populate it for real.

**Brief ref:** 3.5, Section 6 (`/evidence/`), D24, D30, D32.

## W. Phase 9: porting the notebooks into `src/cua/`

(Numbering confirmed against `git log`/`grep "^### D"` immediately before writing this: D92 is the
current highest number. This section continues from D93.)

### D93 — Package layout, a shared `config.py`, pytest scoped to `tests/`, and where the CAPTURE-half glue lives

**Question:** Porting five notebooks (`agent.ipynb`, `02_artifact_schema.py`, `03_recorder.py`,
`04_replay_engine.py`, `05_replay_live.py`) into `src/cua/` is a straight logic port, but a few
real packaging decisions still had to be made: how to avoid re-duplicating the same config/JS
constants a third time now that plain imports are available; how to structure the stateful
`DiscoveryAgent` given the notebooks' own reliance on module-level globals across cells; where the
recorder's CAPTURE-half event-wrapping glue (`extract_value`/`open_path`/`finish_business_outcome`,
the `.coroutine` wrapper, `request_value`/`request_missing_values` synthesis) should live, given
this port's own hard requirement that `cua.recorder` stay pure Python with no Playwright import;
and a real, unrelated bug found while writing the test suite.

**Chosen, one decision at a time:**

1. **A new `src/cua/config.py`** holds `BASE`/`ALLOWED_HOSTS`/`SECRETS`/`APP_ID`/
   `SESSION_EXPIRED_TEXT`/`MODEL`/`resolve_secret`/`host_allowed` — the identical config cell
   duplicated three times across `agent.ipynb` Setup 1, `03_recorder.py` OFFLINE 1 + BROWSER 1, and
   `05_replay_live.py` Setup 1/3. A notebook cell cannot import another notebook, so the
   duplication there was necessary; a real package can just import one module. This is a pure
   packaging improvement (CLAUDE.md's own rule, "ParaBank values live in config... only", is
   satisfied more strongly, not differently) — no rule, guard, or constant value changed.
2. **`DiscoveryAgent` (`src/cua/agent.py`) is a class, not a set of functions closing over module
   globals.** Every mutable global the notebook relied on (`TYPED`, `GIVEN`, `RESULT`, `DECLINED`,
   `LOGIN_ATTEMPTS`/`LOGIN_BLOCKED`, `HANDBACK`) is now an instance attribute of one
   `DiscoveryAgent`, built by an `async def build_agent(page=None, ...)` factory (no top-level
   `await`, matching the async-def-wrapping pattern already used elsewhere this session for running
   these notebooks as scripts). Every safety rule, JS string, and order of operations is unchanged;
   only the state's home changed, from module globals to `self`.
3. **`cua.live.PlaywrightReplaySurface` takes a `DiscoveryAgent` instance directly, rather than
   duplicating `PlaywrightSurface`/lock JS/`human_takeover`/`needs_human` a second time the way
   `05_replay_live.py` necessarily does.** The notebook's own duplication of these was a real
   constraint (a notebook exec context cannot import another notebook's cells except by re-running
   their source, which `04_replay_engine.py`'s/`03_recorder.py`'s own `load_schema()` technique
   already does for the schema); a package has no such constraint. Replay never calls any of
   `DiscoveryAgent`'s LLM-tool methods (`click`, `type_text`, ...) — it only reuses the same
   lower-level mechanics underneath them (`.surface`, `.human_takeover`, `.needs_human`,
   `.current_value`, `.approval_info`), exactly the subset `05_replay_live.py`'s own "Setup 6"
   comment names by hand ("the tool-INDEPENDENT mechanics only").
4. **The recorder's CAPTURE-half event-wrapping glue is NOT part of `cua.recorder`'s importable
   API.** `cua.recorder` (the COMPILE half: `compile_run`, `synthesize_human_entries`,
   `save_capability`, ...) has no `import playwright` anywhere in it, matching this port's own
   scoping instruction. The three additive tools (`extract_value`, `open_path`,
   `finish_business_outcome`) and the `.coroutine`-wrapping event logger live in `src/cua/cli.py`
   instead, built directly against a `DiscoveryAgent` instance and calling `cua.recorder`'s pure
   functions (`classify_status`, `norm_url`, `synthesize_human_entries`) to produce the same event
   shape `03_recorder.py`'s own BROWSER cells produce. This was an explicit instruction ("Leave the
   CAPTURE half... as agent-side code your discover CLI command orchestrates... rather than
   something with an independent importable API of its own") rather than a judgment call: the
   alternative (a `cua.recorder.build_capture_tools(agent)` function) would have made `cua.recorder`
   depend on `cua.agent`/Playwright transitively, defeating the "pure Python, no Playwright import"
   property this phase explicitly asked `cua.recorder`/`cua.replay` to keep.
5. **`pyproject.toml` scopes pytest discovery to `testpaths = ["tests"]`.** Found directly, not
   guessed: running `uv run pytest` with no scoping, in THIS working directory (not a fresh clone),
   collected and executed `notebooks/scratch/_live_preflight_gate_test.py` — a git-ignored,
   per-developer scratch file (matching pytest's own default `*_test.py` discovery pattern) left
   over from an earlier live session, whose top-level code launches a real Chromium browser and
   hits the real `parabank.parasoft.com` on import. This is exactly what this phase's own hard
   rules forbid ("You must NEVER launch a browser, touch ParaBank, or use an API key"). A fresh
   clone would never have this file (`notebooks/scratch/` is git-ignored), so the *deliverable*
   ("fresh clone, `uv run pytest` passes with no key") was never actually at risk — but the
   discovery scope was still the right fix regardless: this port's own test suite lives entirely in
   `tests/`, and pytest should never depend on what a contributor happens to have sitting,
   uncommitted, in a git-ignored scratch directory.
6. **A genuine, pre-existing, unrelated bug found while porting `tests/test_schema.py`:**
   `notebooks/02_artifact_schema.py`'s own Section 2b offline checks assume
   `artifacts/examples/get_account_balance.yaml` has 3 `outcome_rules` (indices 1 and 2 used for a
   "recoverable rule without action"/"hard rule with an action" check) — true when that cell was
   written, no longer true after the example was simplified to one business rule during the D63-D66
   schema rebuild. Confirmed directly, not assumed: `uv run python notebooks/02_artifact_schema.py`
   crashes today with `IndexError: list index out of range` at that exact cell, meaning this
   notebook currently does NOT print "ALL CHECKS PASSED" if run top to bottom. Not fixed in the
   notebook (out of scope: "do not modify any notebook's actual logic," and the notebook was
   already broken before this port touched anything). `tests/test_schema.py` instead builds a
   fixture with the 3-rule shape the check actually needs, so the SAME two `Capability`-level
   validation rules are tested (not weakened, not skipped) without depending on the example
   artifact's current, simplified shape.

**Reasoning:** every one of 1-4 is a structural packaging choice with no effect on any rule,
guard, safety check, or business decision described elsewhere in this file — verified by porting
every offline check from all five notebooks into `tests/` (143 tests, `uv run pytest`, 0 failures,
zero API key/browser/network) and cross-checking each assertion's expected value against the
notebook's own. 5 and 6 are both real findings from doing the port, not hypothetical: 5 is a live
safety-relevant discovery (a real, if inadvertent, path to a browser launch during `pytest`), and
6 is a real, reproducible bug in existing, unmodified notebook code.

**Brief ref:** Section 6 (README: how to run without live services), Section 7 (code quality),
CLAUDE.md's own hard rules for this task (never launch a browser, never touch a notebook's logic).

## X. Phase 5 live bugfix: `escalate`'s hard-failure notification re-triggered the very failure it was reporting

(Numbering confirmed against `git log`/`grep "^### D"` immediately before writing this: D93 was
just taken by the concurrent Phase 9 port. This section continues from D94.)

### D94 — `escalate` must tell "approval gate" and "failure notification" apart by more than the step's shape

**Question:** Running the Phase 8 element-missing error demo live (D92's own checklist item 6 —
remove `transfer_funds`' Transfer button, then replay `{"amount": "20.00"}`, a SAFE amount well
under the $500 auto-approve limit) crashed instead of returning the documented `FAILED`:

```
ResolutionError: primary: role='button' name='Transfer'; fallback: 2th <input> within 'form'
  ... (raised again, uncaught, inside make_escalate's own escalate() closure)
```

`04_replay_engine.py` calls `escalate(reason, ctx)` from two structurally different places for a
risky-click step: once *before* the click, to ask permission (the `amount >= auto_approve_limit`
branch, `ctx` carries `"amount"`/`"limit"`), and once *after* a `ResolutionError` on that same
step, purely to make an already-decided `FAILED` visible to a human watching the browser (the
generic `except ResolutionError` handler). `05_replay_live.py`'s `make_escalate` (D79, D85) told
these apart with `step.action == "click" and step.risk == "risky"` — true for BOTH calls, since a
risky click's target can fail to resolve too. On the approval-gate branch, it re-resolves the
target itself (`ref = await resolve_target_async(live_surface, step.target)`) to build a nice
button name for the decision bar's title — but for the failure-notification call, the target is
*already known* not to resolve (that is the failure being reported), so this re-resolve raises the
identical `ResolutionError` again, uncaught, inside `escalate` itself, instead of the clean
`FAILED` `ReplayResult` the engine was one line away from returning.

**Chosen:** add `"amount" in ctx` to the check. That is the one real, structural difference
between the two call sites (confirmed by reading both call sites in `04_replay_engine.py` Section
9, not guessed) — the approval-gate call always carries the amount and limit it is gating on; no
other `_call_escalate` call site in that file ever does.

**Reasoning:** the fix stays inside `05_replay_live.py`, exactly where D79/D85/D88/D89 already
live — `04_replay_engine.py`'s own `escalate` contract (a plain `Callable[[str, dict], Any]`,
Section 8) is untouched, so this is a live-wiring correction, not an engine change. An alternative
— have `04_replay_engine.py` pass an explicit `kind: "approve"` / `kind: "notify"` tag in every
`ctx` — would be more self-documenting, but touches the shared, already-tested engine and every
existing `_call_escalate` call site for a distinction only this one live consumer currently needs;
rejected as more invasive than the bug warrants. `ctx["amount"]` already exists for exactly the
right reason (D38's amount-vs-limit gate) and happens to double as the discriminator — using it is
not fragile parasitism, it is the same signal `run_capability_async` itself uses to decide whether
to gate at all.

**Verified live, not just reasoned about:** ran the exact element-missing scenario twice against
the real ParaBank site — once before the fix (crash, `ResolutionError` propagating out of
`asyncio.run`), once after (`REPLAY RESULT: FAILED step_index=3 step_action='click' ...`, matching
`evidence/README.md`'s own documented expectation for this demo exactly). The evidence folder this
bug was found while producing (`evidence/replay/transfer_funds-error-element-missing/`) is itself
the fixed behavior's proof, not a fixture.

**Cost, honestly stated:** the generic failure-notification branch (`await _show_decision("REPLAY
needs your attention", reason)`) still blocks on a real human click of any of the three buttons —
that is by design (D28: hold the session open for a human to see what happened), but it means an
unattended/scripted replay that hits *any* hard failure on a risky-click step, or a checkpoint/
retry-exhausted failure the engine also routes through `escalate`, will hang waiting for that click
unless something is watching. Not a new gap this fix introduces — it is `escalate`'s existing,
documented design for every hard failure — but the element-missing crash had been masking it: a
script that crashes loudly is easier to notice than one that hangs quietly forever.

**Brief ref:** 3.6 (a well-reasoned handoff mechanism), D28, D38, D79, D85, D88, D89, D92.

### D95 — `03_recorder.py`'s BROWSER 12 cell used `create_deep_agent` without ever importing it

**Question:** Producing a real discovery-side evidence capture (D92's checklist item 1) meant
actually running `03_recorder.py`'s CAPTURE half end to end for the first time this session
outside of the two RUN cells the notebook's own author had already exercised. `recorder_agent =
create_deep_agent(...)` (BROWSER 12) raised `NameError: name 'create_deep_agent' is not defined`.
`agent.ipynb`'s own STEP 4 has `from deepagents import create_deep_agent` right above its own
`create_deep_agent(...)` call; BROWSER 12's own header comment says it's "copied verbatim" from
that cell, but the import line itself was never carried over — a real, reproducible gap in the
CAPTURE half that nothing had exercised until this run needed the agent to actually exist.

**Chosen:** add the one missing import line, in place, where `agent.ipynb` has it.

**Reasoning:** this is a one-line omission with a one-line fix — no design question here. Worth
recording only because it is a genuine bug this session found live (not a hypothetical), in a file
whose CAPTURE half is otherwise still lightly exercised end to end compared to its COMPILE half
(D70's own honest gap: "capture has touched a real browser at least once... but never got far
enough to prove a real capture-to-compile round trip end to end" — this run is the first time it
has, successfully, past that point).

**Verified:** re-ran all 32 `OFFLINE` cells (unaffected, still pass byte-identical) plus a full
live `BROWSER` run afterward — real login, real `type_secret` x2, real click, real `extract_value`,
real `compile_run` producing both a `login_parabank`-shaped and a task capability, saved as real
`evidence/discovery/20260927-get-account-balance-discovery/` (see D92's own `evidence/` section for
the layout; `events.json` confirmed to carry only secret NAMEs, `"username"`/`"password"`, never
values).

**Brief ref:** D70 (the honest gap this closes), D92 (the evidence this run produced).

### D96 — `build_agent`'s own wiring passed `DiscoveryAgent` a keyword argument it doesn't have

**Question:** The project owner ran `cua discover "Log in and read the balance of account 18672." --name my_balance_check` for real — the very first live run of the Phase 9 CLI port — and it crashed immediately: `TypeError: DiscoveryAgent.__init__() got an unexpected keyword argument 'goal_text'`. `src/cua/agent.py`'s `DiscoveryAgent` is a dataclass whose field is named `given_text` (matching `agent.ipynb`'s own `GIVEN["text"]` global, D33-era naming); `build_agent(page=None, goal_text: str = "", ...)` correctly names ITS OWN parameter `goal_text`, but then constructed `DiscoveryAgent(page, goal_text=goal_text, auto_limit=auto_limit)` — passing the wrong keyword name to the class it was building.

**Why the 143-test suite never caught this:** `tests/test_agent.py` never calls `build_agent` at all (confirmed by `grep`) — correctly, since `build_agent` either launches a real browser (`page=None`) or needs a real `Page` object, both outside what an offline test can do. `DiscoveryAgent` itself is tested directly, with the correct `given_text=` keyword, which is why every existing test passed while this one specific wiring line was never exercised until a real live run needed it. This is the exact same class of gap as D95 (a CAPTURE/live-only code path nothing had run end to end yet) and D70 before it.

**Chosen:** one-line fix, `given_text=goal_text` instead of `goal_text=goal_text`. No API change to `build_agent`'s own signature — its parameter is correctly named `goal_text` from the caller's point of view (matching the CLI's own `--goal`-shaped argument); only the internal pass-through to `DiscoveryAgent` was wrong.

**A second, real finding from the same live run, not a bug but worth recording:** the goal text used ("Log in and read the balance of account 18672.") does not mention `extract_value`, so the agent read the balance via `page_text()` and answered in plain English ("Account 18672 has a balance of $515.50") rather than calling `extract_value(label=..., save_as=...)`. The compiled capability was therefore syntactically valid but practically useless — `outputs: []`, and its only steps were `navigate` to the overview page followed immediately by clicking "Log Out." `compile_run` did exactly what it should with what it was given; the goal simply never told the agent to produce something structured to compile. Every prior successful discovery capture in this project's history (including D92's own evidence run) phrased the goal to explicitly say "Use extract_value to save it as 'balance'" — this is not stated anywhere in the CLI's own `--help` text or its one example. Not fixed as part of this decision (a documentation/UX gap, not a code bug); flagged here so it isn't lost, and a good candidate for a `README.md`/`--help` wording improvement.

**Verified live:** re-ran `uv run pytest` (143 passed, unaffected) and `cua discover "Log in and read the balance of account 18672. Use extract_value to save it as 'balance'." --name ...` was NOT re-attempted with the corrected phrasing in this session (the plain "read the balance" phrasing already proved the actual bug fix works — the crash is gone, the agent completes, `compile_run`/`save_capability` run to completion); the practically-useless capability produced by the first (unfixed-phrasing) run was deleted, not committed.

**Brief ref:** D70, D95 (the same class of live-only gap), D33 (`given_text`'s own naming history).

### D97 — `cua replay` gets a `--login` flag; each invocation otherwise starts a fresh, logged-out browser

**Question:** Trying to replay a freshly-discovered `get_account_balance`-shaped capability via
`cua replay artifacts/get_account_balance_discovery_demo.yaml` failed immediately: `FAILED
step_index=1 ... observed='neither primary nor fallback resolved'`, with `step 0: recoverable
condition matched (action=relogin)` printed first. The capability itself was fine -- it has no
login step of its own, by design (D45's login split: nearly every real capability in this project
assumes an already-logged-in session). The real problem is structural: `cua replay`'s own
`_run_replay` calls `build_agent()` with no `page`, so it launches a brand-new, logged-out browser
on every single invocation. Two separate `cua replay` commands never share a session, so there was
no way to run `login_parabank` first and have that session carry into a second command -- unlike
the notebook, where both cells run in the same Jupyter kernel/browser tab.

**Chosen:** a new `--login <path>` argument on `cua replay`. When given, `_run_replay` calls
`live.replay_live` on the login capability FIRST, with the SAME `agent_run` (same browser/page)
that the main capability then reuses -- one process, one browser, two capabilities in sequence,
mirroring exactly what running two notebook cells back to back already does. A login capability
takes no non-secret inputs, so it's called with `{}`. If the login replay does not return
`SUCCESS`, the command aborts before ever attempting the main capability (never proceeds on a
guess that login "probably" worked).

**Reasoning:** this is the CLI's own missing piece, not a schema or engine change -- `replay_live`
already accepted an `agent` parameter precisely so it COULD be called more than once against the
same session; `cua replay` just never exposed a way to do that from the command line before now.
An alternative (auto-detect a `login_*.yaml` in the same directory and use it implicitly) was
considered and rejected: implicit chaining would silently pick a login file the user did not name,
for a project whose whole design philosophy elsewhere (D29, D68's own refusals) is to fail loudly
and explicitly rather than guess.

**Verified live:** `cua replay artifacts/get_account_balance_discovery_demo.yaml --login
artifacts/login_parabank.yaml` -- login `SUCCESS`, then the main capability's own extract step ran
in the SAME already-logged-in session, reaching a real `SUCCESS` (once D97-adjacent label issue
below was also fixed).

**A second, related finding from the same debugging session:** the freshly-discovered capability's
own `extract` step used `label: Total`... originally `label: Balance` -- the exact same D89 trap
(the Accounts Overview table's `<th>Balance*</th>` header, whose next-sibling cell is a second
header, "Available Amount", not any real value), but hit again because D89's fix repointed one
already-existing FILE (`artifacts/get_account_balance.yaml`), not the underlying pattern -- any
NEW discovery run that reads this same page and has the agent choose `label='Balance'` for its own
`extract_value` call will keep hitting this identically, since nothing in `compile_run` validates
that a `labeled_value` locator's live "next sibling" reading actually produces the declared output
type at compile time. Fixed for this one file (repointed to `Total`, matching D89); the deeper,
general fix -- teaching the recorder to notice a `labeled_value` extract whose recorded value
doesn't look like the declared type, or to prefer a footer/total-row match over a header match when
both exist -- is NOT done, and is flagged here rather than silently left to recur a third time.

**Brief ref:** D45 (login split), D89 (the first instance of the label trap), D91 (the pre-flight
gate this flag composes with cleanly -- both run before any browser action a capability's own steps
would take).

## Y. Phase 9 live bugfix: `extract_value` called repeatedly instead of once during `cua discover`

### D98 — `cli.py`'s own `extract_value`/`open_path` were missing `agent.py`'s own parallel-tool-call lock

**Question:** `03_recorder.py`'s BROWSER 9 wraps `extract_value`/`open_path`/`finish_business_outcome`
the same way `agent.py`'s own `build_tools()` wraps every one of its base tools: with a lock
(`one_at_a_time`, closing over `agent._act_lock`) that serializes tool execution when the model
requests more than one tool call in the same turn. This lock exists specifically because a prior
live bug showed PARALLEL tool calls (`langgraph`'s own tool-execution node runs multiple
same-turn tool calls concurrently via `asyncio.gather`) corrupting agent state during login. Does
`src/cua/cli.py`'s own port of these three tools (`_new_tools`) carry the same lock?

**Found:** no. `_new_tools` defined `extract_value`/`open_path`/`finish_business_outcome` as plain
`@tool(parse_docstring=True)` functions with no `one_at_a_time` wrapper at all -- a real,
structural gap between this port and `03_recorder.py`'s BROWSER 9, in the same family as D95/D96/D97
(a live-only gap the 143-test offline suite cannot see, since none of these tools' bodies are
exercised without a real page).

**Chosen:** restore the lock. `_new_tools` now defines its own `one_at_a_time` (identical shape to
`agent.py`'s, closing on the SAME `agent._act_lock` instance) and applies it to `extract_value` and
`open_path` (not `finish_business_outcome`, matching `03_recorder.py`'s BROWSER 9 exactly -- that
one ends the run, nothing else can race it meaningfully the way a login field or a navigation can).

**Verified:** `uv run pytest` still 143/143 (this cannot be exercised offline; the lock only
matters under real concurrent tool calls against a real page). Re-tested live after this fix: the
`extract_value`-called-repeatedly bug (see D99) still reproduced identically (3 calls) -- this was
a real, worth-keeping fix for a real gap, but NOT the cause of that bug. Kept regardless; see D99
for the actual cause and fix.

**Brief ref:** D73 (the three new tools), agent.ipynb's own login-race-condition history (the
original reason `one_at_a_time` exists at all).

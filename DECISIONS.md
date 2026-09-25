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

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

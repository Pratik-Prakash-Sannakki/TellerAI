# Productionize Plan: notebooks → `src/cua/` package

> **Historical.** This migration is done (2026-10-01): the notebooks are now the `src/cua/`
> package. Kept for the record; code and tests still cite its section numbers. Current docs:
> [docs/README.md](README.md).

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (one fresh
> sub-agent per step below, run in order) with superpowers:test-driven-development, and
> superpowers:verification-before-completion before any "done". Steps use `- [ ]` checkboxes.

**Goal:** Turn `notebooks/discovery/discovery.py` (2329 lines) and `notebooks/replay/replay.py`
(1670 lines) into one typed, importable, generic package with a CLI; notebooks become thin demos.

**Architecture:** Shared layers (`schema`, `vision`, `browser`, `safety`, `handoff`) sit under two
consumers (`discovery`, `replay`). The capability schema is the one contract. Module globals become
two explicit objects: a `Session` (the browser) and a per-run state (`DiscoveryRun` / `ReplayRun`).

**Tech stack:** Python 3.12, uv, Playwright (async), RapidOCR + OpenCV, Pydantic v2, deepagents /
LangChain, pytest + pytest-asyncio, mypy, ruff, black (100).

**Spec:** the lead-engineer brief (this run) + `notebooks/discovery/decisions.md`,
`notebooks/replay/DECISIONS.md`, `discovery_architecture.md`, `replay_architecture.md`.

## Global constraints
- Behaviour identical. A port moves code; it never "improves" logic in the same step.
- Only host `parabank.parasoft.com`; no site value in engine code (site values in `configs/`).
- Secrets: names only in code/logs/model context (D32). `.env` stays the only value source.
- File ≤ 500 lines, function ≤ 40, ≤ 6 params, nesting ≤ 3, complexity ≤ 10.
- No `Any` in signatures; `Protocol` for interfaces; `@dataclass(frozen=True)` for immutable data.
- Everything stays async. The library never calls `asyncio.run` (notebooks own their loop).
- Every step ends with the whole suite green and `graphify update .` run.

## Review focus (failure modes no single step's tests naturally cover)
1. Take-over timing: Done / toolbar hand-back while a send is held at the gates. Pin with the ported
   `test_takeover.py` + `test_handback*.py`, run against the unified `ControlWindow`.
2. A held form POST blocks every page call: no new code inside `guard_send` may touch the page.
   Pin with a test: a `FakePage` whose every method raises while a route is held.
3. Notebook kernel re-run: running the setup cell twice must reuse the open `Session`, not leak a
   browser. Pin with `open_session(existing=...)` test on a fake.
4. Discovery artifact → replay: every saved YAML in `notebooks/discovery/artifacts/` still loads.
   Pin with an integration test that loads all of them.
5. State leaks across runs: values wiped after each run (R7, banking). Pin: after `run_goal` /
   `replay` returns, the run object holds no input values, given text or look.

---

## 1. Package tree

```
src/cua/
  README.md            map of the package, read top to bottom
  __init__.py          version only
  config.py            env + typed config: SiteProfile (loaded from configs/<site>.yaml),
                       BrowserConfig, DiscoveryConfig, ReplayConfig (frozen dataclasses)
  llm.py               make_chat_model (was models.py; the re-export shim was later removed)
  schema/              THE CONTRACT. Pure Pydantic / dataclasses, no I/O
    capability.py      Strict, Target (OcrText/Anchor/TableCell), steps, Input/Output, Capability,
                       CapabilityMeta; SCHEMA_VERSION = 2
    value_types.py     SHAPES, TYPES, value_matches_type
    result.py          Status (StrEnum), Stop, ReplayResult
    events.py          Event TypedDict: the discovery event log entry
  vision/              pixels → text. Pure except take_look
    look.py            Box, Element, Look, encode/decode
    ocr.py             cached RapidOCR engine, ocr(), number(), draw_numbered()
    canvas.py          to_canvas, canvas_size(look), to_page(look, point)
    crops.py           crop_box, cut_crop, read_near, spot_changed, screens_same, element_at
    table.py           same_line … append_rows (the shared OCR table reader)
    screenshot.py      take_look(page, cfg, on_look=None) -> Look
  browser/             Playwright, no decisions
    session.py         Session dataclass + open_session(): context, site page, control page, ext
    site_lock.py       SiteLock (CDP Input.setIgnoreInputEvents)
    input.py           act(), into_box(), wait_for_change()
    dropdown.py        SELECT_AT_POINT_JS, SELECT_AT_INDEX_JS, DROPDOWNS_JS, choose_option()
  safety/              what may leave the tab
    hosts.py           host_allowed(url, profile)
    request.py         sent_fields, rebuilt, pretty, _flat/_json
    mismatch.py        mismatches(fields, given_text), dropdown_options(...)
    send_guard.py      SendGuard: Gate 1 (Approve/Edit), Gate 2; SendState Protocol + hooks
    redact.py          norm, is_sensitive, hide_secrets, redactor, flag_leaks, mask_png
  handoff/             a human in the loop
    control_window.py  ControlWindow (one class, union of both sides' modes) + form rows
    extension.py       ext_call, button_clicked, handback_button (the Chrome toolbar button)
    takeover.py        shared take-over loop: unlock, watch Done/button, re-lock, snap
  discovery/           LLM learns a task once
    README.md
    run.py             DiscoveryRun (was HandoffState) + run_goal()
    agent/             prompt.py (VISUAL_SYSTEM_PROMPT, PROMPT_VERSION), middleware.py
                       (NoopPromptCaching, LatestScreenshotOnly), build.py (build_agent)
    tools/             __init__.py build_tools(ctx) -> list[BaseTool]; guard.py (one_at_a_time,
                       FAILED, step budget); observe.py; act.py (click, type_text, type_secret,
                       select_option, scroll, open_path); read.py (extract_value, extract_table,
                       labels, table_cell); human.py (finish_business_outcome,
                       request_missing_values, ask_human, human_help, human_fills)
    recorder/          events.py (step_events, without_* filters, mark_submits), checkpoint.py,
                       build.py (to_step, build_capability), save.py (save_artifact, describe)
    evidence.py        save_evidence (discovery folder layout)
  replay/              no LLM, deterministic
    README.md
    run.py             ReplayRun (was ReplayState) + replay() entry
    loader.py          load_capability, load_outcomes, inputs (given/ask/fill/secret_name)
    locate.py          rungs: table cell, OCR text, anchor, template; locate(), find()
    steps.py           do_navigate … do_extract_table, ACTIONS
    engine.py          walk, run_step, judge, finish, cleanup
    rescue.py          rescue, hand_back, re-login recovery
    evidence.py        save_evidence (replay folder layout)
  evidence.py          shared: _clean, _png, transcript masking helpers
  eval.py              `cua eval`'s report: summarize, render, save (pure)
  cli.py               `cua discover`, `cua replay`, `cua eval`
configs/parabank.yaml  start_url, allowed_hosts, secret env names, deny/login words, login
                       failure texts, outcome rules. The ONLY place ParaBank lives
```
Each folder gets a `README.md`: what is here, read order, what it may import. Import rule
(enforced by a test): `schema`, `vision` import nothing from cua; `browser`→vision; `safety`,
`handoff`→schema/vision/browser; `discovery`/`replay` never import each other.

## 2. De-duplication (checked by AST diff of both notebooks)

| Piece | Today | Shared home |
|---|---|---|
| 45 defs byte-identical: Box/Element/Look, ocr, number, draw_numbered, hide_secrets, crops, norm, is_sensitive, SEND_GATE, _flat/_json, SiteLock, table reader (12 fns), SHAPES/TYPES, _num/mask_png/_clean/_png | copied | the module in §1 that names them |
| Schema | replay `exec`s discovery's cell via `ast` | `schema/capability.py`, imported by both |
| `take_look` | discovery adds start-log bookkeeping | `vision.screenshot.take_look(on_look=)`; discovery passes its hook |
| `to_canvas`/`canvas`/`to_page` | read `HANDOFF.look` vs `STATE.look` | take `look` as a parameter |
| `Config` | two overlapping dataclasses | `BrowserConfig` (shared fields) + per-side configs |
| `guard_send` | 62 vs 50 lines, same gates | `SendGuard` + `SendState` Protocol; hooks: `on_request` (replay: sent/gated/takeover path), `on_sent` (discovery: redact, log, sent dropdowns); decline text from config |
| `mismatches` | given = goal+answers vs inputs+edits | `mismatches(fields, given_text)`; state supplies text |
| `dropdown_options` | async vs sync, both read the stash | one sync function |
| `ControlWindow`/`_CONTROLS` | ~47 lines differ (help/text vs rescue, `who`) | one class, all modes, `who` param |
| `SELECT_AT_JS` | contains-match + index return vs exact-match by index | two named constants in `browser/dropdown.py` (unify = open question) |
| `redactor` | discovery has `mask=` | discovery version (superset) |
| `snap`, `ext_call` | timeout styles differ | one `snap(page, cfg)`; one `ext_call` |
| `host_allowed`, `SECRETS` | 3 copies incl. `cua/config.py` | `safety/hosts.py` + `config.py` |

## 3. State: globals → explicit objects

| Global | Becomes | Owner |
|---|---|---|
| `page`, `control_page`, `context`, `pw`, `EXT` | `Session` (frozen dataclass) | `browser/session.py` |
| `LOCK`, `CONTROL` | `Session.lock`, `Session.control` | built in `open_session` |
| `CFG`, site constants | `Session.cfg`, `Session.site: SiteProfile` | `config.py` |
| `HANDOFF` | `DiscoveryRun` (mutable dataclass, fresh per run) | `discovery/run.py` |
| `STATE`, `LAST_RUN` | `ReplayRun`; `LAST_RUN` → fields returned with the result | `replay/run.py` |
| `ACT_LOCK`, `SEND_GATE` | `asyncio.Lock` fields on the run / `SendGuard` | created inside the running loop |
| `OCR_ENGINE`, `REFS`, `NAVS` | `functools.cache` engine; counters on the run | vision / run |

- **How tools get state:** `Ctx = (session, run)`, a small frozen dataclass. `build_tools(ctx)`
  returns closures decorated with `@tool`; `build_agent(ctx, model)` wires them. Replay functions
  take `ctx` as the first parameter. No hidden module state.
- **No big bang:** pure functions move first (no state at all). Stateful functions move one layer
  per step, gaining a `ctx`/`look` parameter; their body is otherwise copied unchanged.
- **Notebook re-run:** `open_session(existing)` reuses a live session (today's `"page" in globals()`).
- `SendState` Protocol (`allow_send, takeover, given, look, dropdowns, verdict, given_text()`) is
  satisfied by both run classes, so the guard never knows which side it serves.

## 4. Async and typing
- All I/O async as today. OCR stays inline in step 1 (identical timing); moving it to
  `asyncio.to_thread` is a separate, opt-in step (open question).
- `mypy --strict` on `schema`, `vision`, `safety`, `recorder`, `replay`, `config`, `cli`.
- Relaxed, with reason, per-module in `pyproject.toml`:
  `discovery.agent`/`discovery.tools` (`disallow_untyped_decorators = false`: LangChain `@tool`
  and middleware generics are untyped); `cv2`, `rapidocr` (`ignore_missing_imports`: no stubs).
- No `Any`: images are `NDArray[np.uint8]`; JSON is pydantic `JsonValue`; events are a TypedDict.
- Add `ruff`, `black`, `mypy`, `pytest-asyncio` to the dev group; config in `pyproject.toml`.

## 5. Notebooks after the move
`notebooks/discovery/discovery.py` (+ `.ipynb`) and `notebooks/replay/replay.py` shrink to ~5
cells each: setup (`session = await open_session(load_site("parabank"))`) → run (`await run_goal`
/ `await replay`) → save (artifact, evidence). Top-level `await` works as today. Design docs stay
beside them; the package READMEs link to them.

## 6. Tests
- Shared fakes in `tests/fakes.py`: `FakePage`, `FakeRoute`, `FakeControl`, `mk_look`, `make_ctx`.
  They replace the `ast` + `SimpleNamespace` global injection.
- `tests/unit/` mirrors the package; `tests/integration/` holds offline round trips. All offline.

| Old (tests/discovery/…, tests/replay/…) | New |
|---|---|
| d/test_canvas, d/test_latest_screenshot (vision half), d/test_spot_changed | unit/vision/ |
| d/test_extract_table, d/test_label_values, d/test_read_runs | unit/vision/test_table.py, unit/discovery/tools/test_read.py |
| d/test_transaction_gates, d/test_send_settle, d/test_sent_dropdowns, d/test_no_values_stored, r/test_checks (send part) | unit/safety/ |
| d/test_control_form, d/test_handback, d/test_human_help, d/test_extension_manifest, r/test_handback_button, r/test_handback_manifest, r/test_takeover | unit/handoff/ (+ side-specific halves in unit/discovery, unit/replay) |
| d/test_into_box, d/test_choose_option, d/test_select_anchor, r/test_select_index, r/test_adjacent_selects | unit/browser/ |
| d/test_observable, d/test_wandering, d/test_login_click_kept, d/test_prompt_rules, d/test_latest_screenshot (middleware) | unit/discovery/{tools,agent}/ |
| d/test_save_artifact | unit/discovery/recorder/ |
| d/test_evidence, r/test_replay_evidence | unit/discovery/test_evidence.py, unit/replay/test_evidence.py |
| r/test_load_inputs, r/test_caller_inputs, r/test_resolve_inputs | unit/replay/test_loader.py |
| r/test_rungs, r/test_table_replay | unit/replay/test_locate.py |
| r/test_extract_pattern, r/test_extract_types, r/test_partial_outputs | unit/replay/test_steps.py |
| r/test_engine, r/test_outcomes, r/test_cleanup, r/test_http_errors, r/test_checks | unit/replay/test_engine.py, test_rescue.py |
| r/test_round_trip | integration/test_discovery_to_replay.py (+ every saved YAML loads) |
| test_models.py | unit/test_llm.py |
| new | unit/test_import_rules.py, unit/test_no_site_values.py (grep src for parabank) |

Old test files are deleted in the same step their code moves, so the count never drops silently:
each step reports `before → after` test counts.

## 7. ML-engineering practices (kept small)
| Practice | How |
|---|---|
| Versioned artifact | `schema_version: 2` stays a `Literal`; loader refuses unknown versions with a clear error |
| Capability = model artifact | YAML + crops are the trained output; discovery = "training", replay = "inference" |
| Run logs | evidence folders = experiment logs; add `run.json`: prompt version, model name, config hash, git sha |
| Deterministic replay | no LLM, fixed viewport, rungs logged as drift |
| Config in one place | `configs/<site>.yaml` + `config.py` dataclasses |
| Prompts as versioned constants | `PROMPT_VERSION` in `discovery/agent/prompt.py`, written to evidence (not the artifact) |
| **Stretch:** eval hook | `cua eval cap.yaml --runs N` → status counts + rung histogram (flakiness) |

## 8. Migration order (strictly sequential; one sub-agent per step; notebooks untouched until step 10)
The notebooks stay the frozen reference while the package grows. Each step: port code + its
tests + folder README, run `uv run pytest`, `mypy`, `ruff`, `graphify update .`, stop.

| # | Step (owner = one fresh sub-agent) | Files it alone owns |
|---|---|---|
| 0 | Tooling: dev deps, mypy/ruff/black/pytest-asyncio config, `tests/fakes.py`, baseline count | pyproject.toml, tests/fakes.py |
| 1 | `schema/` + `config.py` split + `configs/parabank.yaml`; `models.py`→`llm.py` shim | src/cua/schema/, config.py, llm.py, configs/ |
| 2 | `vision/` pure modules (look, ocr, canvas, crops, table) | src/cua/vision/ |
| 3 | `discovery/recorder/` (pure: events → Capability → YAML) | src/cua/discovery/recorder/ |
| 4 | `replay/loader.py` + `locate.py` (pure) | those two files |
| 5 | `browser/` + `vision/screenshot.py`: `Session`, `open_session`, lock, input, dropdown | src/cua/browser/, vision/screenshot.py |
| 6 | `safety/`: unified `SendGuard` + `SendState`, mismatch, redact, hosts | src/cua/safety/ |
| 7 | `handoff/`: unified `ControlWindow`, extension, take-over loop | src/cua/handoff/ |
| 8 | `discovery/` run, tools, agent, evidence; `build_tools(ctx)` | rest of src/cua/discovery/ |
| 9 | `replay/` run, steps, engine, rescue, evidence; shared `cua/evidence.py` | rest of src/cua/replay/, cua/evidence.py |
| 10 | Thin notebooks + `cli.py` + `[project.scripts] cua`; integration tests | notebooks/*/*.py+.ipynb, cli.py, tests/integration/ |
| 11 | Docs: root README/REPORT paths, CLAUDE.md section, delete `tests/discovery|replay` leftovers | README.md, REPORT.md, CLAUDE.md |
| 12 | **DONE (2026-10-01).** `cua eval --runs N`: status counts + rung histogram + fallback steps | cli.py, src/cua/eval.py |
The user runs the browser cells after step 10 (live check of both notebooks) before step 11.

**Status (2026-10-01): steps 0-12 done, committed.** Step 12 (`cua eval`) was built after the
migration, as decided.

## 9. Risks
| Risk | Guard |
|---|---|
| Take-over timing changes (Done vs held send, button poll) | step 7 ports the take-over tests first (red), unified class must pass both sides' suites; no timing constants change |
| CDP lock not re-applied after an error | `SiteLock.open()` stays the only unlock path; test that an exception inside re-locks |
| Page call while a send is held hangs the run | Review-focus test 2; `SendGuard` gets no page handle at all, only state |
| Locks created outside the running loop | `asyncio.Lock`s live on objects built inside `open_session`/run, never at import |
| Notebook event loop | library never calls `asyncio.run`; only `cli.py` does |
| Unifying near-duplicates changes behaviour | each unified piece keeps both sides' old tests; differences become explicit parameters |
| Schema import path changes break saved YAML | integration test loads every saved artifact |
| Secret value reaches a log via the new `ctx` | ported `test_no_values_stored` + leak test on evidence output |

## 10. Line-count offenders (today)
| Item | Now | Limit | Fix |
|---|---|---|---|
| `discovery.py` / `replay.py` | 2329 / 1670 lines | 500 | split per §1; largest new file (`discovery/tools/act.py`) est. ~250 |
| discovery `guard_send` | 62 | 40 | `SendGuard` methods: `_confirm_mismatch`, `_gate1`, `_gate2`, `_after_send` |
| replay `guard_send` | 50 | 40 | same class |
| discovery `take_over` | 44 | 40 | shared loop in `handoff/takeover.py` + discovery hook |
| discovery `click` | 44 | 40 | extract `_risky_click` / `_landing` helpers |
| `VISUAL_SYSTEM_PROMPT` | 52-line constant | n/a | fine as data in `prompt.py` |
| `ControlWindow` | 70 / 73 lines | 300, 7 public | check public-method count in step 7; split form rendering if > 7 |
| params | none > 6 | 6 | — |

## Open questions (user's call)
1. Site config as `configs/parabank.yaml` (proposed) or a Python `SiteProfile` constant?
2. Unify the two `SELECT_AT_JS` variants into one script, or keep both named constants (proposed)?
3. Move OCR to `asyncio.to_thread` (your async rule) as an extra step, accepting a timing change?
4. Rename `models.py` → `llm.py` (with a re-export shim), to free "models" for schemas?
5. Prompt version + model in evidence only (proposed), or also in the artifact (needs schema v3)?
6. Keep artifacts under `notebooks/discovery/artifacts/` or move to a top-level `artifacts/`?


## Decisions (user, 2026-10-01)
1. Site values: **YAML** (`configs/parabank.yaml` → frozen `SiteProfile`).
2. Dropdown JS: **keep both**, named `SELECT_AT_POINT_JS` / `SELECT_AT_INDEX_JS`.
3. OCR: **`asyncio.to_thread`**; take-over tests guard the timing change.
4. `models.py` → **`llm.py`**, with a 1-line `models.py` re-export shim.
5. Prompt/model version: **evidence only** (`run.json`); schema stays v2.
6. Artifacts: **top-level `artifacts/`** (`artifacts/<name>.yaml`, `artifacts/crops/<name>/`).
7. `cua eval --runs N`: **DONE** (step 12, after the migration). Replays a capability N times in
   one session, reports status counts + rung histogram + fallback steps (`src/cua/eval.py`).

## Restore: TypeSafe tool selection + model routing (user, 2026-10-01)
Planned in `notebooks/discovery/PLAN.md` (D50/D52/D76) but never wired into the visual notebook, then
deleted with `src/cua/agent.py` in 4f692a8. Restore in step 8 as `src/cua/discovery/agent/routing.py`:
- Source: `git show 4f692a8^:src/cua/agent.py` lines ~1140-1240 (`NEVER_HIDE`, `JOB_EXTRA_TOOLS`,
  `JOB_CRITERIA`, `job_tool_names`, `confidence_gate`, `build_typesafe_middleware`).
- Re-map jobs to the VISUAL tools (observe, click, type_text, type_secret, select_option, scroll,
  open_path, extract_value, extract_table, finish_business_outcome, request_missing_values,
  ask_human); `NEVER_HIDE` keeps observe/click/type_secret/ask_human.
- Confidence < 0.8 or any error -> fail open (all tools). Model router: Haiku for simple steps,
  Sonnet otherwise, both via `cua.llm.make_chat_model`.
- Off unless `TYPESAFE_API_KEY` is set. It sends the page path + last result text to typesafe.ai:
  never on with real data. Re-add `langchain-typesafe` as an OPTIONAL extra in pyproject.
- Tests: no key -> []; low confidence -> all tools; job map covers every visual tool.

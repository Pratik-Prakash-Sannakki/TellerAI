# Architecture: Agent + Discovery Pipeline

This doc diagrams how the system is actually built (`src/cua/` + the phase notebooks it was ported
from), and flags one honest gap between the assignment brief and this implementation: **the brief
assumes a heterogeneous, often-legacy, not-necessarily-clean DOM (Section 3.7 / glossary
"Heterogeneous, Often Legacy Surfaces" / "The Real Environment"); this implementation is built and
tested against ParaBank, a real but structurally clean, modern Bootstrap DOM.** That gap is
already logged in `DECISIONS.md` (D22's own "Known cost" note, quoted at the bottom of this doc) —
it was not missed, it was accepted and the mitigation is the `Surface` seam, not a claim that the
seam was ever exercised against a dirty DOM.

## 1. High-level component architecture

```mermaid
flowchart TB
    subgraph Human["Human"]
        H1["Discovery goal text<br/>(plain English)"]
        H2["Approve / Reject / Take-over<br/>(decision bar)"]
    end

    subgraph Discovery["Discovery (agent, LLM-in-the-loop)"]
        DA["DiscoveryAgent<br/>(src/cua/agent.py)"]
        LOOP["LOOK -&gt; THINK -&gt; ACT loop<br/>(deep agent / LangChain tools)"]
        TOOLS["Tool methods:<br/>click, type_text, type_secret,<br/>select_option, extract_value,<br/>request_value, ask_human,<br/>human_takeover, open_path,<br/>finish_business_outcome"]
        SAFE["Safety layer:<br/>one_at_a_time lock<br/>host_allowed allowlist<br/>risky-click deny-by-default"]
        DA --> LOOP --> TOOLS
        TOOLS --> SAFE
    end

    subgraph SurfaceGroup["Surface abstraction (D22 - the seam)"]
        SURF["Surface interface<br/>observe / act / resolve"]
        PWS["PlaywrightSurface<br/>(the ONLY implementation built)"]
        SURF --- PWS
    end

    subgraph Recorder["Recorder (COMPILE half - pure Python, no Playwright)"]
        EVT["Event log<br/>(one entry per tool call)"]
        CLEAN["clean_events / drop_detours /<br/>drop_dead_end_risky_clicks /<br/>split_login / trim_tail"]
        SYN["synthesize_human_entries<br/>(turn a human handoff into a<br/>real type_text/select_option event)"]
        BUILD["build_steps -&gt; Target primary/fallback<br/>(role &gt; label &gt; text &gt; structure)"]
        COMPILE["compile_run<br/>-&gt; Capability or CompileError"]
        EVT --> CLEAN --> SYN --> BUILD --> COMPILE
    end

    subgraph Artifact["Structured Artifact"]
        CAP["Capability (schema.py)<br/>steps, inputs, outputs,<br/>Target locators, OutcomeRule,<br/>checkpoint, risk_level"]
        YAML["artifacts/*.yaml"]
        CAP -->|to_yaml| YAML
    end

    subgraph Replay["Replay (deterministic, NO LLM)"]
        RUN["run_capability /<br/>run_capability_async"]
        RESOLVE["resolve_target /<br/>resolve_target_async<br/>(walks primary, then fallback)"]
        OUTCOME["_check_outcomes<br/>Business / Recoverable / Hard<br/>3-way taxonomy (D10)"]
        RESULT["ReplayResult<br/>SUCCESS / BUSINESS_OUTCOME /<br/>NEEDS_APPROVAL / FAILED"]
        RUN --> RESOLVE
        RUN --> OUTCOME --> RESULT
    end

    subgraph EscalateGroup["Human-in-the-loop escalation"]
        ESC["make_escalate<br/>(src/cua/live.py)"]
        BAR["Real Approve/Reject/Take-over<br/>decision bar (Playwright UI)"]
        ESC --- BAR
    end

    Browser["Real browser<br/>(parabank.parasoft.com only)"]

    H1 --> DA
    TOOLS -.->|act / observe / resolve| SURF
    PWS -->|Playwright API calls| Browser
    TOOLS --> EVT
    YAML -->|loaded via from_yaml| RUN
    RESOLVE -.->|act / observe / resolve| SURF
    RUN -->|risky click needs approval| ESC
    ESC --> H2 --> BAR
    BAR -->|approved click, or reject, or<br/>human takes the browser| RUN
    TOOLS -->|ask_human / request_value /<br/>human_takeover| H2
```

Key point for the clean-DOM question: **every arrow that touches the real page** — `TOOLS` acting,
`RESOLVE` resolving a locator, the decision bar rendering — goes through the `Surface`
interface's single implementation, `PlaywrightSurface`. That interface is the intended point where
a legacy/non-clean surface (desktop accessibility API, a vision-only surface, a dirtier DOM with no
stable `id`s or `role`s) would plug in without touching `DiscoveryAgent`, the recorder, or the
replay engine. **It was designed for that, but never tested against anything other than ParaBank's
own clean DOM** — see the callout at the bottom.

## 2. How discovery actually happens (sequence)

```mermaid
sequenceDiagram
    participant User
    participant Agent as DiscoveryAgent
    participant Tools as Tool methods
    participant Browser as PlaywrightSurface
    participant Events as Event log
    participant Recorder as compile_run()
    participant YAML as Capability YAML

    User->>Agent: goal text ("Log in and read\nthe balance of account 18672.\nUse extract_value to save it.")
    loop LOOK-THINK-ACT, one step at a time (one_at_a_time lock)
        Agent->>Browser: observe() -> screenshot + numbered elements
        Browser-->>Agent: numbered DOM snapshot
        Agent->>Tools: decide next tool call\n(click / type_text / type_secret / extract_value / ...)
        Tools->>Browser: act(action, target) or resolve(locator)
        Browser-->>Tools: result (success, value, or needs_human)
        Tools->>Events: log one event\n(tool name, args, resolved target,\nlabel_header/value_header flags D101/D102)
        opt risky action (e.g. a submit button)
            Tools->>User: ask for approval (deny-by-default, D33)
        end
        opt agent unsure / stuck
            Tools->>User: ask_human() / request_value() / human_takeover()
        end
    end
    Agent->>Recorder: finish_business_outcome() / end of run
    Recorder->>Events: clean_events(), drop_detours(),\ndrop_dead_end_risky_clicks(), split_login(), trim_tail()
    Recorder->>Recorder: synthesize_human_entries()\n(a human handoff becomes a real,\nreviewable type_text/select_option step)
    Recorder->>Recorder: build_steps()\n-> Target(primary, fallback) per element\n-> refuses if a labeled_value resolved\nto a header cell (D101/D102)
    Recorder->>YAML: compile_run() -> Capability -> to_yaml()
    Recorder-->>User: Capability saved, or CompileError\n(refuses rather than guesses)
```

## 3. The clean-DOM gap, explicitly

The brief's glossary and Section 3.7 assume "Heterogeneous, Often Legacy Surfaces" and describe
"The Real Environment" as one where DOMs are not guaranteed clean or stable. This project's real
target — ParaBank — is a real, live, third-party site, but its DOM is a modern, well-structured
Bootstrap table/form layout: stable `id`s, real `<label for>` associations, real `role`s. The
locator strategy (`role > label > text > structure`, D8) and the whole `Target(primary, fallback)`
model (D63) were built and tested against exactly that kind of DOM.

`DECISIONS.md` says this plainly, and this diagram is the place to repeat it rather than let it stay
buried:

> **Known cost:** the DOM is clean, so the legacy/no-clean-DOM story cannot be *shown* in code; it
> is argued in the report through the `Surface` seam (D22) and the ranked locators (D8). Also,
> being a third-party server, we cannot force failures on demand; we inject faults browser-side
> instead (D30).
> — `DECISIONS.md`, line 74

So the architecture's answer to "what if the DOM isn't clean" is a **design argument**, not a
**demonstrated** one:
- `Surface` (D22) is a real interface with one real implementation (`PlaywrightSurface`); a second
  implementation (desktop accessibility API, or a vision-based fallback) was never written, so the
  interface's shape is inferred from the one clean-DOM case it was actually built against.
- The ranked locator strategy (`role > label > text > structure`, falling back through weaker
  signals) is the mechanism meant to survive a messier page, but it has only ever been exercised on
  pages where `role`/`label` were already reliable — a dirtier page (no `role`s, duplicate/absent
  labels, D68's own stated gap) would fall to `structure`/`text` far more often, and that path is
  far less tested.
- Section 7 explicitly does not reward building tenant/legacy plumbing, and D64 went further and
  removed even the placeholder schema fields (`app.id`/`app.vendor`/`base`/`overrides`) that once
  gestured at it — so heterogeneity is now a pure prose argument in `REPORT.md`, with literally no
  schema surface backing it.

**Bottom line:** the architecture is *designed* to generalize past a clean DOM (that's what the
`Surface` seam and ranked locators are for), but everything actually built, tested, and evidenced in
this repo only proves it against ParaBank's clean one. That's a real, disclosed limitation, not a
silent one — but it is a limitation.

# cua.replay

No LLM, deterministic: runs a capability discovery saved. Step 4 lands only the pure parts --
loading the artifact and locating a target on screen. Step 9 adds `run.py`, `steps.py`,
`engine.py`, `rescue.py`, `evidence.py`.

## Read order
1. `loader.py` - `load_capability` (YAML -> `Capability`, viewport/host/input/secret/crop checks),
   `load_outcomes` (a capability's own `outcomes:` or the site's defaults), `seen_outcome` (R17
   taxonomy match), `given_inputs`/`fill`/`secret_name`/`step_inputs` (the caller's values into
   `{{name}}` placeholders; secrets stay as placeholders until typed).
2. `locate.py` - the rungs: `same_text`/`typed_ok`/`same_label` (fuzzy-but-exact-on-digits text
   match), `find_text`, `find_template` (rung 3), `read_cell` (table cell), `anchor_point`
   (rung 2), `text_hit` (rung 1, duplicate-text tiebreak), `locate` (point, rung) from the first
   rung that hits. `find` (scrolls the page, async) is not here -- it needs a live `Page`.

Globals the notebook read off `CFG`/`SECRETS` are explicit parameters here: `site: SiteProfile`
and `cfg: BrowserConfig` into `load_capability`; `site: SiteProfile` into `load_outcomes`;
`cfg: ReplayConfig` threaded through every `locate.py` function.

## What may NOT go here
- Never import `cua.discovery` (and discovery never imports this).
- No Playwright import, no LLM call, no site value (those live in `configs/<site>.yaml`).
- `ask_inputs`/`ask_option` (need the control window) and `find` (scrolls a live page) are not
  this step -- step 9.

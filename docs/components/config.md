# Config and site profiles

Every site-specific value lives in one YAML file per site. The code holds none. A second bank (or
tenant) is a new file, not a code change. This doc also covers the run settings and secrets.

## Where it lives

- [`src/cua/config.py`](../../src/cua/config.py): `SiteProfile`, `load_site`, `BrowserConfig`,
  `DiscoveryConfig`, `ReplayConfig`, `OutcomeRule`, model names, `resolve_secret`,
  `secret_values`, and a re-export of `host_allowed`. Loads `.env` at import (`load_dotenv`).
- [`configs/parabank.yaml`](../../configs/parabank.yaml): the only ParaBank values in the repo.
- [`configs/rails/`](../../configs/rails/): the NeMo guardrail files ([guardrails](guardrails.md)).
- `.env` (git-ignored; template [`.env.example`](../../.env.example)): secret values and API keys.

## How it works

- `load_site(name)` reads `configs/<name>.yaml` and returns a frozen `SiteProfile`. The repo root
  is the nearest folder with a `configs/` folder, above the package or the working directory.
- It validates as it loads:
  - `outcomes[].status` must be `BUSINESS_OUTCOME`, `RECOVER` or `FAILED`.
  - `allowed_actions` must be a subset of the step actions; unknown names fail at load.
  - `rails` must be `off`, `on` or `required` (an unquoted YAML `on`/`off` boolean is mapped back).
- The CLI picks the profile with `--site`. Without it, `default_site()` uses the only
  `configs/*.yaml` there is, and exits asking for `--site` when there are several.
- Secrets: the profile maps a secret NAME to an env-var NAME (`secret_env`). `resolve_secret(name,
  site)` reads the value from the environment and raises on an unknown name or an empty value.
  `secret_values(site)` builds the in-memory name -> value map ("" when unset).

### Site profile keys

| Key | Meaning | Default |
|---|---|---|
| `name` | profile name | the file stem |
| `start_url` | where every run starts; `base_url` is it without the trailing `/` | required |
| `allowed_hosts` | the host lock ([safety](safety.md)) | required |
| `secret_env` | secret name -> env var name | `{}` |
| `deny_words` | clicks and paths with these words are refused | `[]` |
| `login_words` | the login button's text; its POST skips the send gates | `[]` |
| `allowed_actions` | step actions discovery may perform and replay may run | all 7 site actions |
| `login_failure_texts` | discovery: login failed, stop | `[]` |
| `login_empty_texts` | discovery: the boxes were empty, retry once | `[]` |
| `outcomes` | replay: text seen after a step -> status; first match wins | `[]` |
| `id_min_digits` / `id_visible_digits` | account-id masking (`98765` -> `***765`) | 5 / 3 |
| `rails` | NeMo input rail mode | `on` |

`allowed_actions` covers `navigate`, `click`, `type`, `select`, `scroll`, `extract`,
`extract_table`. A dropdown-options read (`extract_options`) counts as `extract` on both sides.

### Run settings (frozen dataclasses, code defaults)

| Class | Knobs |
|---|---|
| `BrowserConfig` | `viewport` (1280, 800), `ocr_min_score` 0.5, `scroll_px` 600, `same_screen_mad` 1.0, `crop_pad`, `point_crop`, `settle_ms` 600, `sensitive_words` (password, ssn, social), `ext_s`, `ext_poll_s` |
| `DiscoveryConfig` | `send_wait_ms`, `snap_ms`, `handback_s` 120, `login_limit` 3, `repeat_limit` 3, `unsure_limit` 3, `step_budget` 40, `run_timeout_s` 900 |
| `ReplayConfig` | `fuzzy` 0.8, `template_threshold` 0.8, `template_margin` 0.05, `scroll_retries` 1, `check_s` 5.0, `poll_ms`, `snap_s`, `page_s`, `gate_s` 120, `field_min`, `short_value`, `near_px` 60 |

Model names: `SONNET_MODEL_NAME`, `HAIKU_MODEL_NAME` ([LLM and routing](llm-and-routing.md)).

### Multi-tenant

- Built: one profile per site, picked with `--site`. Capabilities are per site: replay refuses
  one whose `base_url` host is not in the profile's `allowed_hosts`.
- Designed, not built: a per-tenant overlay YAML over a base capability that replaces only the
  changed steps (REPORT §4).
- Steps to add a site: README, "Configure the bank, or swap in another one".

## Public API / key types

`load_site`, `SiteProfile`, `OutcomeRule`, `BrowserConfig`, `DiscoveryConfig`, `ReplayConfig`,
`resolve_secret`, `secret_values`, `host_allowed`, `STEP_ACTIONS`, `OUTCOME_STATUSES`.

## Safety and guarantees

- No site value in `src/`: `tests/unit/test_no_site_values.py` fails on `parabank`/`parasoft`
  anywhere in `src/`.
- Secret values are read from the environment only, never from a profile or a capability.
  `resolve_secret`'s errors name the env var, never its value.
- Every config object is frozen; `run.json` records a hash of them per run ([evidence](evidence.md)).

## Tests

- `tests/unit/test_config.py` (profile values, outcome order, validation, secrets, defaults,
  `allowed_actions`, `rails` modes).
- `tests/unit/test_no_site_values.py`.
- `tests/unit/test_cli.py` (`default_site`, `--site`).

## Limits and cuts

- The page must render at 1280x800, scale 1; replay refuses other sizes (Q10, R3).
- Login is assumed to be a username + password form.
- Tenant overlays are design only.

## Decisions

- Q10 (window size and zoom) in [discovery-decisions.md](../decisions/discovery-decisions.md).
- R3 (screen size), R9 (hosts, secrets, site code), R17 (outcome statuses) in
  [replay-decisions.md](../decisions/replay-decisions.md).

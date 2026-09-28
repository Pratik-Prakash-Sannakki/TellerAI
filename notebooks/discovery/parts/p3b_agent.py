# %% OFFLINE 21: LangChain tool wrappers (one call at a time) + the pure-visual guard
import ast
import functools
import inspect as _inspect

from langchain.tools import tool

HUMAN_HAS_CONTROL = "REFUSED: human has control. Wait until they click Done, then call observe."

_TOOL_DOCS: dict[str, str] = {
    "observe": """Look at the screen: a fresh screenshot, read by OCR, with numbered text boxes.

Returns:
    Each numbered text with its box. Numbers change after every action; use the latest list.
""",
    "click": """Click the text box with this number on the latest screen.

Every click needs a human's Approve unless it is on the safe list; the system asks by itself.

Args:
    ref: Number of the text box on the latest screen.

Returns:
    The new screen, or REFUSED / STALE / DECLINED / NO CHANGE. After DECLINED, never retry.
""",
    "click_at": """Click a point that has no text (an empty input box, an icon, a checkbox).

Args:
    x: Pixels from the left edge of the screenshot.
    y: Pixels from the top edge of the screenshot.

Returns:
    The new screen, or NO CHANGE if nothing happened.
""",
    "type_text": """Type a value into a box, given by number or by point (empty boxes have no number).

Only values from the goal are typed; any other value goes to a human.

Args:
    value: The exact text to type, copied from the goal.
    ref: Number of the box, if it shows text.
    x: Point of an empty box, pixels from the left.
    y: Point of an empty box, pixels from the top.

Returns:
    The new screen, or a refusal. A human-entered value is never shown to you.
""",
    "type_secret": """Type a stored secret by its NAME. You never see the value.

Args:
    name: The secret's name, e.g. username or password.
    ref: Number of the box, if it shows text.
    x: Point of an empty box, pixels from the left.
    y: Point of an empty box, pixels from the top.

Returns:
    OK with the new screen, or REFUSED / STOP.
""",
    "scroll": """Scroll to see things that are not on the screen. Old numbers go stale.

Args:
    direction: up or down.
    x: Optional point over a scrolling panel, pixels from the left.
    y: Optional point over a scrolling panel, pixels from the top.

Returns:
    The new screen with new numbers, or TOP / BOTTOM OF PAGE.
""",
    "select_option": """Pick an option in a dropdown, by the dropdown's number or point.

Args:
    option: The option text, copied from the goal.
    ref: Number of the dropdown.
    x: Point of the dropdown, pixels from the left.
    y: Point of the dropdown, pixels from the top.

Returns:
    The new screen, or ASK_HUMAN when the option is not in the goal or could not be chosen.
""",
    "open_path": """Open a page on the allowed site directly, e.g. /overview.htm.

Args:
    path: A path starting with /. Query values must come from the goal.

Returns:
    The new screen, or REFUSED.
""",
    "extract_value": """Save a value you can see (a balance, a confirmation number).

Args:
    ref: Number of the value's text box (the value itself, never a column header).
    save_as: A short snake_case name for the value.
    value_type: One of string, integer, number, currency, date.
    description: One sentence on what the value is.

Returns:
    OK with the saved value, or REFUSED.
""",
    "finish": """End the run. Log out first.

Args:
    summary: What happened. Start with STUCK: or DECLINED: when that is why the run ended.

Returns:
    FINISHED. Stop after this.
""",
    "finish_business_outcome": """End the run as a known business outcome shown on the screen.

Args:
    outcome: A short UPPER_SNAKE name, e.g. ACCOUNT_NOT_FOUND.
    proof_text: The exact message text copied from the current screen.

Returns:
    FINISHED, or REFUSED if the text is not on the screen.
""",
    "ask_human": """Ask a human a question in the control window. Not for missing values.

Args:
    question: One short question.

Returns:
    The human's typed answer. The human never touches the site.
""",
    "request_value": """Ask a human for ONE field's value; our code types it in.

Args:
    label: The field's name as you read it on the screen.
    ref: Number of the field, if it shows text.
    x: Point of an empty field, pixels from the left.
    y: Point of an empty field, pixels from the top.

Returns:
    OK (the value is never shown to you), SKIP if already filled, or DECLINED.
""",
    "request_missing_values": """Ask a human for EVERY empty field on this page, in one go.

Args:
    fields: One entry per empty field: its point (x, y) and your label for it (hint).

Returns:
    One line per field: OK, SKIP or DECLINED, then the new screen. Values are never shown.
""",
    "take_over": """Hand the live session to a human. ONLY when truly stuck: the last action had
no effect and no other tool can express what is needed (an odd popup, a CAPTCHA).

Args:
    reason: What blocks you, in one sentence.

Returns:
    REFUSED if you are not stuck, or the fresh screen after the human clicks Done.
""",
}

TOOL_NAMES = frozenset(_TOOL_DOCS)


def _free_tool(name: str) -> Callable[..., Awaitable[str]]:
    """The free `async def name(st, ...)` tool from the cells above, found by name."""
    fn = globals()[name]
    assert _inspect.iscoroutinefunction(fn), name
    return fn


def _as_tool(st: AgentState, name: str, gate: asyncio.Lock) -> object:
    """One LangChain tool over the free function `name`, with `st` bound and the model-facing
    docstring. Refused while a human holds control; otherwise one call at a time (`gate`)."""
    fn = _free_tool(name)
    params = list(_inspect.signature(fn).parameters.values())[1:]   # drop `st`

    async def wrapper(**kwargs: object) -> str:
        if _human_has_control(st):
            return HUMAN_HAS_CONTROL
        async with gate:
            if _human_has_control(st):
                return HUMAN_HAS_CONTROL
            return await fn(st, **kwargs)

    wrapper.__name__ = wrapper.__qualname__ = name
    wrapper.__doc__ = _TOOL_DOCS[name]
    wrapper.__signature__ = _inspect.Signature(params, return_annotation=str)
    wrapper.__annotations__ = {p.name: p.annotation for p in params} | {"return": str}
    return tool(parse_docstring=True)(wrapper)


def build_tools(st: AgentState) -> list:
    """Every free tool as a LangChain tool over `st`, one call at a time.

    The per-call gate is its OWN lock, not st.act_lock: act() already takes st.act_lock around
    each site action, and asyncio.Lock is not re-entrant, so reusing it here would deadlock.
    (cua.agent's `one_at_a_time` is a closure inside DiscoveryAgent.build_tools, so it cannot be
    imported; this is the same pattern: one lock around the whole tool call.)"""
    gate = asyncio.Lock()
    return [_as_tool(st, name, gate) for name in _TOOL_DOCS]


print("OK OFFLINE 21")


# %% OFFLINE 22: the visual system prompt + the optional TypeSafe middleware
from cua.agent import JOB_EXTRA_TOOLS, NEVER_HIDE, build_langchain_agent, build_typesafe_middleware  # noqa: F401

VISUAL_SYSTEM_PROMPT = """You are an expert browser operator on a banking demo site. You see the screen ONLY as a picture read by OCR: every tool result lists numbered text boxes with their positions. You act only with the mouse and keyboard, through these tools.

## Tools
- observe: take a fresh look. Call it first, and again whenever you are unsure.
- click(ref): click a numbered text (a button, a link, a menu item).
- click_at(x, y): click a point with NO text: an empty input box, an icon, a checkbox. Empty boxes have no number, so point at them.
- type_text(value, ref or x,y): type a value from the goal into a box. Empty boxes: give the point.
- type_secret(name, ref or x,y): type a stored secret by NAME (username, password). You never see the value.
- scroll(direction): for things you cannot see. Old numbers go stale; use the new ones.
- select_option(option, ref or x,y): pick a dropdown option from the goal.
- open_path(path): open a page on the site directly.
- extract_value(ref, save_as, value_type, description): save a value you need (a balance). Point at the value, never at its column header.
- request_value(label, ref or x,y): ask a human for ONE field's value; our code types it.
- request_missing_values(fields): ask a human for EVERY empty field on this page at once.
- ask_human(question): a question only, when unsure what to do. Not for missing values.
- take_over(reason): ONLY when truly stuck: the last action had no effect and no other tool can do what is needed. A human then works on the live page and hands back.
- finish(summary): end the run. finish_business_outcome(outcome, proof_text): end on a known message shown on the screen.

## How to work
1. Call observe first. If you see a login form, log in with type_secret at the boxes' points, then confirm the account page appears.
2. Refer to things only by the LATEST numbers, or by points on the latest screenshot. Numbers change after every action.
3. Use ONLY values from the goal. Never invent one. If values are missing, FIRST open the page where the task is done, THEN call request_missing_values ONCE. Never ask a human on the start page.
4. If a result says a human entered a value, do not type it again.
5. Every click that is not on the safe list asks a human by itself. If a result says DECLINED, never retry or work around it: log out, then finish with 'DECLINED:'.
6. Make ONE tool call at a time.
7. If you repeat the same action 3 times or are lost, log out and finish with 'STUCK:'. Use take_over only when truly stuck, never for a risky click.
8. Attempt login at most 3 times. If the login could not be verified, stop: finish with 'STUCK:'.
9. Always log out before you finish: happy path, STUCK or DECLINED. Do not leave the session open.
"""

VISUAL_EXTRA_NEVER_HIDE = frozenset({
    "click_at", "type_text", "select_option", "scroll", "extract_value", "open_path",
    "finish_business_outcome", "request_missing_values", "request_value", "ask_human", "take_over"})


class _UrlView:
    """What build_typesafe_middleware reads from its `agent` argument: `agent.page.url`."""

    def __init__(self, st: AgentState) -> None:
        self.page = st.surface


def build_middleware(st: AgentState) -> list:
    """The TypeSafe tool router + model router (D50/D52), or [] with no TYPESAFE_API_KEY.
    Its fast/powerful models are `cua.models.make_chat_model("haiku"/"sonnet")` (Iliad gateway)."""
    return build_typesafe_middleware(_UrlView(st), extra_never_hide=set(VISUAL_EXTRA_NEVER_HIDE))


print("OK OFFLINE 22")


# %% OFFLINE 21t: tests for OFFLINE 21 (tool set, one-at-a-time, human control, no secret params,
# the pure-visual guard M1, and the cross-part name-collision guard)
import re as _re21

_ARGS21: dict[str, dict] = {
    "observe": {}, "click": {"ref": 1}, "click_at": {"x": 1, "y": 1},
    "type_text": {"value": "a", "ref": 1}, "type_secret": {"name": "password", "ref": 1},
    "scroll": {"direction": "down"}, "select_option": {"option": "a", "ref": 1},
    "open_path": {"path": "/x.htm"},
    "extract_value": {"ref": 1, "save_as": "a", "value_type": "string", "description": "d"},
    "finish": {"summary": "s"}, "finish_business_outcome": {"outcome": "A", "proof_text": "p"},
    "ask_human": {"question": "q"}, "request_value": {"label": "l", "ref": 1},
    "request_missing_values": {"fields": []}, "take_over": {"reason": "r"},
}
_SECRETISH21 = _re21.compile(r"secret|password|passwd|pwd", _re21.IGNORECASE)


class _SlowSurface21(FakeSurface):
    """TEST ONLY: a slow screenshot that records (start, end) times, to see overlapping calls."""
    spans: list[tuple[float, float]] = []

    async def screenshot(self) -> bytes:
        t0 = time.monotonic()
        await asyncio.sleep(0.05)
        self.spans.append((t0, time.monotonic()))
        return await super().screenshot()


def _state21(surface: FakeSurface | None = None) -> AgentState:
    st = _state16([_S1, _S2])
    st.control = FakeControlTO()
    if surface is not None:
        st.surface, st.ocr = surface, surface.ocr
    return st


def _test_21_names_and_params() -> None:
    tools = build_tools(_state21())
    assert len(TOOL_NAMES) == 15 and {t.name for t in tools} == set(TOOL_NAMES)
    assert set(_ARGS21) == set(TOOL_NAMES)
    for t in tools:
        bad = [p for p in t.args if _SECRETISH21.search(p)]
        assert not bad, (t.name, bad)          # a secret VALUE is never a tool parameter
    ts = next(t for t in tools if t.name == "type_secret")
    assert "name" in ts.args and "value" not in ts.args, ts.args


async def _test_21_one_at_a_time() -> None:
    slow = _SlowSurface21([_S1, _S2], _URL16)
    slow.spans = []
    st = _state21(slow)
    obs = next(t for t in build_tools(st) if t.name == "observe")
    outs = await asyncio.gather(obs.ainvoke({}), obs.ainvoke({}))
    assert all(o.startswith("Screen gen") for o in outs), outs
    (a0, a1), (b0, b1) = sorted(slow.spans)
    assert a1 <= b0, f"two tool calls overlapped: {slow.spans}"


async def _test_21_human_has_control() -> None:
    st = _state21()
    tools = build_tools(st)
    st._h20_human = True
    for t in tools:
        assert await t.ainvoke(_ARGS21[t.name]) == HUMAN_HAS_CONTROL, t.name
    assert st.surface.calls == [] and st.control.prompts == [] and st.look is None
    assert not st.log.path.exists() or st.log.path.read_text() == ""
    st._h20_human = False
    assert (await tools[0].ainvoke({})).startswith("Screen gen")


_test_21_names_and_params()
run_sync(_test_21_one_at_a_time())
run_sync(_test_21_human_has_control())

# --- M1 pure-visual guard: no DOM/JS call on the site anywhere in the parts. -------------------
# Exclusions (by exact name, nothing else): the control window is OUR OWN local page, not the site,
# so it may use evaluate/expose_function/set_content:
#   BrowserControlWindow, BrowserControlWindowTO, FakeControlPage, control_html, control_html_to.
# `.content` as a plain attribute (a LangChain message's `m.content`) is not a call and not flagged.
_M1_EXCLUDED = frozenset({"BrowserControlWindow", "BrowserControlWindowTO", "FakeControlPage",
                          "control_html", "control_html_to"})
_AST_FLAGS = ast.PyCF_ALLOW_TOP_LEVEL_AWAIT | ast.PyCF_ONLY_AST


def _part_sources() -> dict[str, str]:
    paths = sorted((HERE / "parts").glob("p[0-6]*.py"))
    assert len(paths) >= 12, paths
    return {p.name: p.read_text() for p in paths}


def _forbidden_attr(attr: str) -> bool:
    return any(attr == f or (f.endswith("_") and attr.startswith(f)) or attr.startswith(f + "_")
               for f in FORBIDDEN_ON_SITE)


def m1_hits(sources: dict[str, str]) -> list[str]:
    """Every `x.<forbidden>(...)` call (and any `.accessibility` access) outside the excluded
    control-window classes/functions, as 'file:line attr'."""
    hits: list[str] = []
    for fname, src in sources.items():
        tree = compile(src, fname, "exec", flags=_AST_FLAGS)
        skip = {id(n) for d in ast.walk(tree) if getattr(d, "name", None) in _M1_EXCLUDED
                and isinstance(d, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                for n in ast.walk(d)}
        for n in ast.walk(tree):
            if id(n) in skip:
                continue
            called = isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
            attr = n.func.attr if called else getattr(n, "attr", None) if isinstance(n, ast.Attribute) else None
            if attr and (_forbidden_attr(attr) if called else attr == "accessibility"):
                hits.append(f"{fname}:{n.lineno} {attr}")
    return hits


# --- name-collision guard: one notebook namespace, so a later part must not silently rebind. ---
_SCRATCH_OK = frozenset({"_png", "_els", "_found", "_ocr", "_shape", "_first", "_k", "_v", "_w",
                         "_texts", "START_URL", "tempfile", "async_playwright"})


def _top_level_names(tree: ast.Module) -> set[str]:
    """Names bound by top-level def/class/assignment (compound statements included, not bodies of
    functions or classes; imports excluded)."""
    names: set[str] = set()
    todo = list(tree.body)
    while todo:
        n = todo.pop()
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
        elif isinstance(n, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = n.targets if isinstance(n, ast.Assign) else [n.target]
            names |= {m.id for t in targets for m in ast.walk(t) if isinstance(m, ast.Name)}
        elif isinstance(n, (ast.If, ast.Try, ast.With, ast.AsyncWith, ast.For, ast.AsyncFor)):
            todo += [*n.body, *getattr(n, "orelse", []), *getattr(n, "finalbody", [])]
            todo += [s for h in getattr(n, "handlers", []) for s in h.body]
    return names


def collisions(sources: dict[str, str]) -> dict[str, list[str]]:
    """name -> the parts that define it, for every name defined in 2+ parts (minus _SCRATCH_OK)."""
    where: dict[str, list[str]] = {}
    for fname, src in sources.items():
        for name in _top_level_names(compile(src, fname, "exec", flags=_AST_FLAGS)):
            where.setdefault(name, []).append(fname)
    return {k: v for k, v in where.items() if len(v) > 1 and k not in _SCRATCH_OK}


_parts21 = _part_sources()
assert m1_hits({"bad.py": "async def f(page):\n    await page.evaluate('1')\n"}) == ["bad.py:2 evaluate"]
assert m1_hits({"bad.py": "x = page.get_by_role('button')\n"}) == ["bad.py:1 get_by_role"]
assert m1_hits({"ok.py": "class FakeControlPage:\n    def f(self, p):\n        p.evaluate('1')\n"}) == []
assert m1_hits({"ok.py": "t = m.content\nawait page.mouse.click(1, 2)\nawait page.keyboard.type('a')\n"}) == []
assert not m1_hits(_parts21), m1_hits(_parts21)
assert collisions({"a.py": "_x = 1\n", "b.py": "def _x():\n    pass\n"}) == {"_x": ["a.py", "b.py"]}
assert collisions({"a.py": "_png = 1\n", "b.py": "_png = 2\n"}) == {}
assert not collisions(_parts21), collisions(_parts21)
print("OK OFFLINE 21t")

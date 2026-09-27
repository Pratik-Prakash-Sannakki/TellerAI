# %% [markdown]
# # Agent 2: an architecture for a non-clean / legacy DOM
# Pure Python. No browser, no network, no API key, no `import playwright`. Run cells top to bottom.
#
# **Why this notebook exists.** `ARCHITECTURE.md` (repo root) diagrams the system built through
# Phase 9 and names its own honest gap: the brief's Section 3.7 / glossary explicitly assume
# "Heterogeneous, Often Legacy Surfaces" and describe "The Real Environment" as one where a DOM is
# not guaranteed clean or stable, but every locator strategy actually built (`role` > `label` >
# `text` > `structure`, D8/D63) was designed AND tested only against ParaBank's own clean, modern
# Bootstrap DOM. `DECISIONS.md` line 74 says this plainly:
#
# > "Known cost: the DOM is clean, so the legacy/no-clean-DOM story cannot be *shown* in code; it
# > is argued in the report through the `Surface` seam (D22) and the ranked locators (D8)."
#
# This notebook stops arguing it in prose and shows it in code: a `FakeLegacyPage` fixture with
# **no `role`, no `aria-*`, no `id`, no `<label for>`** anywhere (an old table-layout HTML form,
# the canonical "legacy web app" shape) -- proving today's `role`/`label` locator strategies
# genuinely fail against it -- and a small resolution ladder of new strategies that succeed anyway,
# with **zero LLM call at replay time** (the same hard rule D6/3.3 already applies to the clean-DOM
# engine). This is `Agent 2`: not a rewrite of `DiscoveryAgent`, but the missing `Surface`-side
# resolution strategies its D22 seam was always meant to host.
#
# **What this notebook is not:** a real legacy target. There is no second `parabank`-shaped site to
# discover against, so -- exactly like D22's own honestly-stated limit -- this is proven with a
# hand-built fixture, not a live run. `Glossary: Accessibility Tree` (Section 10 of the brief,
# linked to 3.1's agent loop) is the brief's own nod to this exact idea: browsers compute
# accessibility info even when a page's markup never asks them to.

# %% [markdown]
# ## The workaround for a legacy application, explained
#
# Today's four locator strategies (`role`, `label`, `text`, `structure`) all read the DOM as
# *authored* -- they need a developer to have written `role=`, `<label for=...>`, or a stable
# `id`/class structure. A legacy app (a 20-year-old JSP/ASP table-layout form, a mainframe-web
# wrapper, a Java-applet-era UI rendered to canvas) usually has none of that. Five things still
# work, in increasing order of how little the markup has to cooperate:
#
# 1. **Computed accessible name, not authored markup.** Every browser already runs an accessible-
#    name-computation algorithm for *every* element, authored or not: `aria-label` -> `<label>` ->
#    `placeholder` -> `title` -> nearest preceding text node -> `value`. Playwright exposes this via
#    `page.accessibility.snapshot()` / the CDP Accessibility domain -- it is not a new invention,
#    just a resolution strategy this codebase has not used yet. A `<td>Name:</td><td><input></td>`
#    table-layout form (no `<label>` tag at all) still gets a computed accessible name of `"Name:"`
#    for that `<input>`, because "nearest preceding text" is one of the algorithm's own fallback
#    rungs. New strategy: **`accessible_name`**.
# 2. **Native HTML tag semantics give an *implicit* role for free.** `<input type="submit">`,
#    `<select>`, `<a href>` all have a browser-computed implicit ARIA role with zero authored
#    `role=` attribute -- legacy apps overwhelmingly use native controls (no custom-widget
#    frameworks to *not* bother annotating), so implicit-role matching is a strictly bigger net than
#    today's `role` strategy, which only reads an explicit `role=` attribute today.
# 3. **Positional anchoring relative to a stable landmark, not a page-root index.** `structure` +
#    `within` (D63) already exists; the legacy extension is anchoring the `within` scope to a
#    landmark that is unlikely to move across a redesign (a page's own `<h1>` text, a table's own
#    header row) instead of counting from the document root, which shifts the moment any earlier
#    markup changes.
# 4. **Deterministic visual re-identification -- no vision LLM, still no LLM at replay time.** At
#    record time, save a tiny signature of the target's own visual neighborhood (this notebook uses
#    a cheap deterministic string signature as a stand-in for a real perceptual hash / OpenCV
#    template match -- the mechanism, not the specific algorithm, is the point). At replay time,
#    compare against the live page's signatures and take the closest match, then act by that
#    element's coordinates. This is the correct last-resort rung for a canvas-rendered or image-map
#    UI that has no DOM structure to read at all.
# 5. **A third locator rung, and a real drift counter, not just two.** D63 deliberately cut the
#    original ranked-locator list down to exactly `primary` + one `fallback`, because a third slot
#    was "never populated" against ParaBank's own clean DOM (D63's own stated reasoning). That
#    empirical justification does not hold for a legacy surface -- level-3+ matches (anchor, visual)
#    are real and expected, not curiosities -- so a legacy-facing `Target` needs a third rung, and
#    D21's own "drift signal" (which locator level matched, tracked over replays) needs to become
#    code, not just a report paragraph, because a legacy page falls to weak locators far more often.
#
# None of this touches `src/cua/schema.py`, `recorder.py`, or `replay.py` -- those stay exactly as
# built for the clean-DOM (ParaBank) case. This notebook is scoped to the `Surface` seam itself
# (D22), which is precisely the seam that was designed, but never exercised, for this.

# %% Section 1: the new locator strategies (pure data, no browser)
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

LegacyStrategy = Literal["accessible_name", "anchor", "visual_template"]


@dataclass(frozen=True)
class AccessibleNameLocator:
    """Strategy 1+2 combined: match by the browser's OWN computed accessible name (which already
    falls back through aria-label -> label -> placeholder -> title -> nearest preceding text ->
    value) and, for a native control, its implicit role. Needs no authored role/label markup."""
    strategy: Literal["accessible_name"] = "accessible_name"
    accessible_name: str = ""
    implicit_role: str = ""  # e.g. "textbox", "button" -- computed from the tag, not an attribute
    note: str = ""


@dataclass(frozen=True)
class AnchorLocator:
    """Strategy 3: the nth <tag> after a stable text landmark, not a page-root index."""
    strategy: Literal["anchor"] = "anchor"
    landmark_text: str = ""
    tag: str = ""
    nth: int = 0
    note: str = ""


@dataclass(frozen=True)
class VisualTemplateLocator:
    """Strategy 4: a deterministic visual signature of the element's own neighborhood, captured at
    record time. Matched at replay time by nearest-signature, never by an LLM call."""
    strategy: Literal["visual_template"] = "visual_template"
    signature: str = ""
    note: str = ""


LegacyLocator = AccessibleNameLocator | AnchorLocator | VisualTemplateLocator


@dataclass(frozen=True)
class LegacyTarget:
    """Strategy 5: a THREE-rung target (primary, fallback, visual_fallback) -- deliberately
    reopening D63's two-rung decision for the legacy surface only. `01_02_...` artifacts for
    ParaBank are completely untouched; this type lives only in this notebook."""
    primary: LegacyLocator
    fallback: LegacyLocator | None = None
    visual_fallback: VisualTemplateLocator | None = None

    def rungs(self) -> list[LegacyLocator]:
        out = [self.primary]
        if self.fallback is not None:
            out.append(self.fallback)
        if self.visual_fallback is not None:
            out.append(self.visual_fallback)
        return out


print("legacy locator types defined:", AccessibleNameLocator.__name__, AnchorLocator.__name__,
      VisualTemplateLocator.__name__, LegacyTarget.__name__)

# %% Section 2: a fake legacy DOM -- no role, no aria-*, no id, no <label for>, anywhere
# This is the fixture the whole notebook proves itself against: an old table-layout HTML form,
# the canonical "legacy web app" shape the brief's 3.7 gestures at. Every element is described only
# by tag, its own visible/placeholder text (if any), a preceding text node (if any), and a position
# within its row -- deliberately nothing a `role`/`label` strategy could use.


@dataclass
class LegacyElement:
    ref: int
    tag: str
    row: int          # which <tr> it lives in
    col: int          # which <td> within that row
    preceding_text: str = ""   # text node immediately before it in the same <td>, if any
    placeholder: str = ""
    value: str = ""
    visual_sig: str = ""       # stand-in for a perceptual hash of its rendered neighborhood


@dataclass
class FakeLegacyPage:
    """A dict-based fake DOM: rows of table cells, each holding at most one control. No id, no
    role, no aria-*, no <label for> anywhere -- proving today's role/label strategies cannot
    resolve anything here, on purpose."""
    title: str
    elements: list[LegacyElement] = field(default_factory=list)

    def by_ref(self, ref: int) -> LegacyElement | None:
        for el in self.elements:
            if el.ref == ref:
                return el
        return None


# The fixture: an old "New Customer" form. Row 0 is the landmark ("Personal Information"); rows
# 1-3 hold Name/Address/Phone inputs, each preceded by its own label TEXT NODE (not a <label> tag).
LEGACY_PAGE = FakeLegacyPage(
    title="New Customer",
    elements=[
        LegacyElement(ref=1, tag="td", row=0, col=0, preceding_text="", value="Personal Information"),
        LegacyElement(ref=2, tag="input", row=1, col=1, preceding_text="Name:", visual_sig="sig-name-row1"),
        LegacyElement(ref=3, tag="input", row=2, col=1, preceding_text="Address:", visual_sig="sig-addr-row2"),
        LegacyElement(ref=4, tag="input", row=3, col=1, preceding_text="Phone:", visual_sig="sig-phone-row3"),
        LegacyElement(ref=5, tag="input", row=4, col=1, preceding_text="", placeholder="submit",
                      value="Submit", visual_sig="sig-submit-row4"),
    ],
)

print("fake legacy page built:", LEGACY_PAGE.title, "| elements:", len(LEGACY_PAGE.elements))

# %% Section 2b: PROVE today's role/label strategies genuinely fail against this fixture
# `resolve_today(...)` reproduces exactly what `RoleLocator`/`LabelLocator` need: an explicit
# `role=`/`aria-*` attribute, or an explicit `<label for=...>` association. `LegacyElement` has
# neither -- there is nothing to read. This is the gap made concrete, not asserted in prose.


def resolve_today_role(page: FakeLegacyPage, role: str, name: str) -> int | None:
    """What RoleLocator needs: an explicit `role=`/native-role ATTRIBUTE. This fixture never sets
    one (LegacyElement has no such field at all) -- so this always returns None here, by design."""
    return None  # no element in this fixture carries an authored role attribute


def resolve_today_label(page: FakeLegacyPage, label: str) -> int | None:
    """What LabelLocator needs: an explicit <label for=...> association. This fixture has none --
    `preceding_text` is a plain text node, not a <label> element -- so this always returns None."""
    return None  # no <label for> exists anywhere in this fixture, by design


assert resolve_today_role(LEGACY_PAGE, "textbox", "Name") is None
assert resolve_today_label(LEGACY_PAGE, "Name:") is None
print("confirmed: today's role/label strategies resolve NOTHING against a legacy-shaped page")

# %% Section 3: the resolution ladder that DOES work here -- deterministic, no LLM call
DriftEvent = tuple[int, LegacyStrategy]  # (ref, which rung matched)


class DriftLog:
    """D21's 'drift signal' made concrete: which locator LEVEL matched, every time. A legacy
    surface is expected to fall to weaker rungs more often; this counts it instead of only arguing
    it in a report."""
    def __init__(self) -> None:
        self.events: list[DriftEvent] = []

    def record(self, ref: int, strategy: LegacyStrategy) -> None:
        self.events.append((ref, strategy))

    def weak_rung_ratio(self) -> float:
        if not self.events:
            return 0.0
        weak = sum(1 for _, s in self.events if s in ("anchor", "visual_template"))
        return weak / len(self.events)

    def should_flag_for_review(self, threshold: float = 0.5) -> bool:
        """D21: a capability that keeps falling to weaker locators is flagged for review, not
        failed silently."""
        return self.weak_rung_ratio() > threshold


def resolve_accessible_name(page: FakeLegacyPage, loc: AccessibleNameLocator) -> int | None:
    """The browser's own accessible-name fallback chain, reproduced for the fixture:
    aria-label (none here) -> label-for (none here) -> placeholder -> nearest preceding text ->
    value. Whichever is present first wins, exactly like a real accessibility tree computes it."""
    for el in page.elements:
        computed = el.placeholder or el.preceding_text or el.value
        if computed.rstrip(":").strip().lower() == loc.accessible_name.rstrip(":").strip().lower():
            return el.ref
    return None


def resolve_anchor(page: FakeLegacyPage, loc: AnchorLocator) -> int | None:
    """Find the landmark row by its own text, then take the nth matching-tag element found in
    rows AFTER it, in row order -- anchored to content, not a page-root index."""
    landmark_row = next((el.row for el in page.elements if el.preceding_text == "" and
                          el.value == loc.landmark_text), None)
    if landmark_row is None:
        return None
    candidates = [el for el in page.elements if el.row > landmark_row and el.tag == loc.tag]
    candidates.sort(key=lambda el: el.row)
    if loc.nth < 1 or loc.nth > len(candidates):
        return None
    return candidates[loc.nth - 1].ref


def resolve_visual_template(page: FakeLegacyPage, loc: VisualTemplateLocator) -> int | None:
    """Nearest-signature match -- a deterministic stand-in for a real perceptual-hash/template-
    match comparison. No model call; exact-match here, nearest-distance in a real implementation."""
    for el in page.elements:
        if el.visual_sig == loc.signature:
            return el.ref
    return None


def resolve_legacy(page: FakeLegacyPage, target: LegacyTarget, drift: DriftLog) -> int | None:
    """Walk primary -> fallback -> visual_fallback, in order, exactly like run_capability's own
    resolve_target does for the clean-DOM engine (04_replay_engine.py Section 5) -- just with three
    rungs and legacy-shaped strategies instead of role/label/text/structure."""
    for loc in target.rungs():
        if isinstance(loc, AccessibleNameLocator):
            ref = resolve_accessible_name(page, loc)
        elif isinstance(loc, AnchorLocator):
            ref = resolve_anchor(page, loc)
        elif isinstance(loc, VisualTemplateLocator):
            ref = resolve_visual_template(page, loc)
        else:  # pragma: no cover - exhaustive by construction
            ref = None
        if ref is not None:
            drift.record(ref, loc.strategy)
            return ref
    return None


print("resolution ladder defined: accessible_name -> anchor -> visual_template")

# %% Section 3b: checks -- the ladder resolves what role/label could not, in increasing difficulty
drift = DriftLog()

# (1) accessible_name rung alone, via the "preceding text node" fallback (no <label> anywhere):
name_target = LegacyTarget(primary=AccessibleNameLocator(accessible_name="Name:", note="preceding text node fallback"))
assert resolve_legacy(LEGACY_PAGE, name_target, drift) == 2

# (2) anchor rung, when accessible_name is deliberately wrong (simulating an OCR/text-extraction
# miss) and only positional anchoring off a landmark still finds it:
addr_target = LegacyTarget(
    primary=AccessibleNameLocator(accessible_name="Street:", note="deliberately wrong on this page"),
    fallback=AnchorLocator(landmark_text="Personal Information", tag="input", nth=2,
                            note="2nd input after the landmark row"),
)
assert resolve_legacy(LEGACY_PAGE, addr_target, drift) == 3

# (3) visual_template rung, as the true last resort when BOTH text-based rungs are wrong (the
# canvas-rendered / image-map case, where there is no text or structure to read at all):
phone_target = LegacyTarget(
    primary=AccessibleNameLocator(accessible_name="Mobile:", note="deliberately wrong"),
    fallback=AnchorLocator(landmark_text="Personal Information", tag="input", nth=99,
                            note="deliberately out of range"),
    visual_fallback=VisualTemplateLocator(signature="sig-phone-row3", note="last resort"),
)
assert resolve_legacy(LEGACY_PAGE, phone_target, drift) == 4

# every rung actually used gets recorded -- one per resolved target above:
assert drift.events == [(2, "accessible_name"), (3, "anchor"), (4, "visual_template")]
assert drift.weak_rung_ratio() == 2 / 3
assert drift.should_flag_for_review() is True  # D21: 2 of 3 resolutions needed a weak rung -> flag

print("resolved via accessible_name, anchor, and visual_template in turn; drift log:", drift.events)
print("weak-rung ratio:", round(drift.weak_rung_ratio(), 2), "-> flag for review:",
      drift.should_flag_for_review())

# %% Section 3c: a target that fails ALL THREE rungs still refuses cleanly, never guesses
missing_target = LegacyTarget(
    primary=AccessibleNameLocator(accessible_name="Fax:"),
    fallback=AnchorLocator(landmark_text="Personal Information", tag="select", nth=1),
    visual_fallback=VisualTemplateLocator(signature="sig-does-not-exist"),
)
assert resolve_legacy(LEGACY_PAGE, missing_target, DriftLog()) is None
print("a target matching nothing on the page still returns None, not a guess")

print("\nALL CHECKS PASSED")

# %% [markdown]
# ## What this notebook does NOT do (honest limits, matching D22's own pattern)
# - **No real legacy site was ever discovered against or replayed against.** `FakeLegacyPage` is a
#   hand-built fixture, the same honest limit D22 itself states for the original `Surface` seam
#   ("only a web surface is built... the report says so"). There is no second real target in this
#   project, so this cannot become more than a fixture-proven design without one.
# - **`visual_template` here is a string equality stand-in**, not a real perceptual hash / OpenCV
#   template match. The mechanism (capture a neighborhood signature at record time, nearest-match it
#   at replay time, no model call) is the actual claim; the specific similarity function is not.
# - **Nothing in `src/cua/schema.py`/`recorder.py`/`replay.py` was touched.** `LegacyTarget` and its
#   three locator types are new, notebook-local types -- wiring them into the real `Capability`
#   schema (as a second `Target` variant, gated by which `Surface` implementation recorded it) is a
#   real schema change and is deliberately out of scope for this exploratory notebook.
# - **The `DriftLog` here is per-run, in memory.** D21's real drift signal would need to persist
#   across replays of the SAME capability over time to be useful; this notebook only shows the
#   counting mechanism working within one resolution pass.

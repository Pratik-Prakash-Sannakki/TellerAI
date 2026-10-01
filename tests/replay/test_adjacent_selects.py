"""Transfer's second dropdown: the 'to account #' anchor must never land on 'From account #', and
a merged 'to account #15120' OCR box must confirm option '15120'."""


def test_from_label_is_not_the_to_anchor(ns) -> None:
    assert not ns["same_label"]("From account #", "to account #")     # 0.85 fuzzy before the fix
    assert not ns["same_label"]("to account #", "From account #")


def test_the_right_label_still_matches(ns) -> None:
    same_label = ns["same_label"]
    assert same_label("to account #", "to account #")
    assert same_label("to account #|15120", "to account #")           # merged with the value
    assert same_label("From account #[", "From account #")
    assert same_label("Log ln", "Log In")                             # a one-letter OCR slip


def test_the_to_anchor_finds_the_to_label_not_the_from_label(ns, mk_look) -> None:
    look = mk_look([("From account #", (488, 346, 578, 364)), ("to account #", (720, 346, 800, 364))])
    el = ns["find_text"](look, "to account #", 1, ns["same_label"])
    assert el is not None and el.text == "to account #"


def test_value_glued_to_hash_confirms_the_option(ns) -> None:
    shows = ns["shows_option"]
    assert shows("to account #15120", "15120")
    assert shows("to account #|15120", "15120")
    assert not shows("to account #151200", "15120")
    assert not shows("to account #15121", "15120")

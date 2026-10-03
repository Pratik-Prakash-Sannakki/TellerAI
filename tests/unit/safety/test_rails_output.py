"""Output rail: what leaves discovery (the final answer) is masked; a credential withholds it."""

from __future__ import annotations

from cua.safety.rails import WITHHELD, check_output
from cua.safety.redact import IdMask

IDS = IdMask(5, 3)


def test_a_clean_confirmation_passes_unchanged() -> None:
    text = "$5.00 has been transferred from account #***778 to account #***778."
    out = check_output(text, IDS)
    assert out.answer == text
    assert not out.withheld
    assert out.hits == ()


def test_an_unmasked_account_id_is_masked() -> None:
    out = check_output("Paid from account 13344.", IDS)
    assert out.answer == "Paid from account ***344."
    assert out.hits == ("account_id",)


def test_a_card_number_is_masked_with_or_without_spaces() -> None:
    for card in ("4111111111111111", "4111 1111 1111 1111", "4111-1111-1111-1111"):
        out = check_output(f"Card {card} on file.", IDS)
        assert card not in out.answer
        assert "card_number" in out.hits
        assert out.answer.endswith("***1111 on file.")


def test_an_ssn_is_masked() -> None:
    out = check_output("SSN 123-45-6789 found.", IDS)
    assert out.answer == "SSN ***-**-6789 found."
    assert out.hits == ("ssn",)


def test_a_password_like_string_withholds_the_answer() -> None:
    out = check_output("Logged in. password: hunter2", IDS)
    assert out.withheld
    assert out.answer == WITHHELD
    assert out.hits == ("credential",)


def test_a_secret_value_withholds_the_answer() -> None:
    out = check_output("Typed s3cretpw into the box.", IDS, {"password": "s3cretpw"})
    assert out.withheld
    assert out.answer == WITHHELD
    assert out.hits == ("secret",)


def test_amounts_and_short_numbers_are_not_pii() -> None:
    text = "Balance $5022.93, 3 accounts, step 12."
    assert check_output(text, IDS).answer == text


def test_a_separated_card_followed_by_more_digits_is_still_masked() -> None:
    for text in ("Card 4111 1111 1111 1111 12/25 on file", "4111-1111-1111-1111 5 items"):
        out = check_output(text, IDS)
        assert "4111" not in out.answer.replace("***1111", "")
        assert "***1111" in out.answer
        assert "card_number" in out.hits


def test_a_card_after_leading_digits_is_masked() -> None:
    out = check_output("ref 12 4111 1111 1111 1111", IDS)
    assert "***1111" in out.answer
    assert "4111 1111" not in out.answer


def test_a_luhn_invalid_long_run_is_not_called_a_card() -> None:
    """By design: only Luhn-valid runs are cards; other long digit runs are ids/references."""
    out = check_output("ref 1234 5678 9012 3456", IDS)
    assert "card_number" not in out.hits
    assert out.answer == "ref 1234 5678 9012 3456"


def test_secrets_none_is_fine() -> None:
    assert check_output("ok", IDS, None).answer == "ok"

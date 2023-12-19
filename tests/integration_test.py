import pytest
from src.emulator.main import say_hi_em
from src.translator.main import say_hi_trans


def test_ci() -> None:
    assert 1 == 1


def test_imports() -> None:
    assert say_hi_em() == say_hi_trans()


@pytest.mark.golden_test("./../golden/*.yaml")
def test_golden_replace(golden) -> None:
    assert str(golden["input"]).replace(" ", "1") == golden.out["output"]

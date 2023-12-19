from src.translator.main import say_hi_trans
from src.emulator.main import say_hi_em


def test_ci() -> None:
    assert 1 == 1

def test_imports() -> None:
    assert say_hi_em() == say_hi_trans()
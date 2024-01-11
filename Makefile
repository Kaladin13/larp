POETRY = poetry run
TEST = pytest --verbose -vv
COVERAGE = coverage
LINT = ruff check --fix --unsafe-fixes .

PYTHON = python3.10

TRANSLATOR = src.translator.main
EMULATOR = src.emulator.main

test:
	$(POETRY) $(COVERAGE) run -m $(TEST)

coverage: test
	$(POETRY) $(COVERAGE) report -m

lint:
	$(POETRY) $(LINT)

translator:
	$(PYTHON) -m $(TRANSLATOR) $(ARGS)

emulator:
	$(PYTHON) -m $(EMULATOR) $(ARGS)

update-golden:
	$(POETRY) $(COVERAGE) run -m $(TEST) --update-goldens
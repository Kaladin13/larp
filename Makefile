POETRY = poetry
POETRY_RUN = $(POETRY) run
TEST = pytest --verbose -vv
COVERAGE = coverage
LINT = ruff check --fix --unsafe-fixes .

PYTHON = python3.10

TRANSLATOR = src.translator.main
EMULATOR = src.emulator.main

poetry:
	$(POETRY) install

test:
	$(POETRY_RUN) $(COVERAGE) run -m $(TEST)

coverage: test
	$(POETRY_RUN) $(COVERAGE) report -m

lint:
	$(POETRY_RUN) $(LINT)

translator:
	$(PYTHON) -m $(TRANSLATOR) $(ARGS)

emulator:
	$(PYTHON) -m $(EMULATOR) $(ARGS)

update-golden:
	$(POETRY_RUN) $(COVERAGE) run -m $(TEST) --update-goldens
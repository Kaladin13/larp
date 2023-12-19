POETRY = poetry run
TEST = pytest --verbose
COVERAGE = coverage
LINT = ruff check --fix .

PYTHON = python3.10

TRANSLATOR = src/translator/main.py
EMULATOR = src/emulator/main.py

test:
	$(POETRY) $(COVERAGE) run -m $(TEST)

coverage: test
	$(POETRY) $(COVERAGE) report -m

lint:
	$(POETRY) $(LINT)

translator:
	$(PYTHON) $(TRANSLATOR)

emulator:
	$(PYTHON) $(EMULATOR)

update-golden:
	$(POETRY) $(COVERAGE) run -m $(TEST) --update-goldens
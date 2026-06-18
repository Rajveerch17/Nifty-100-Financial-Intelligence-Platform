.PHONY: venv install load test lint format clean

PYTHON ?= python
VENV ?= .venv

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(PYTHON) -m pip install -r requirements.txt

load:
	$(PYTHON) -m src.etl.loader

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	ruff check src/ tests/

format:
	black src/ tests/

clean:
ifeq ($(OS),Windows_NT)
	if exist data\nifty100.db del /f data\nifty100.db
	if exist output rmdir /s /q output
else
	rm -f data/nifty100.db
	rm -rf output
endif

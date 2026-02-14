.PHONY: test lint format

test:
	python -m unittest discover -s code/_Tests -p "test_*.py" -v


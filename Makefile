.PHONY: all zip clean format mypy pylint fix
all: zip

PACKAGE_NAME := browser_alphabetic_sort

zip: $(PACKAGE_NAME).ankiaddon

$(PACKAGE_NAME).ankiaddon: src/*
	rm -f $@
	find src/ -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	( cd src/; zip -r ../$@ * -x meta.json )

fix:
	python -m black src
	python -m isort src

mypy:
	python -m mypy src

pylint:
	python -m pylint src

clean:
	rm -f $(PACKAGE_NAME).ankiaddon

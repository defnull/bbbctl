.PHONY: venv clean build release format

venv: .venv/.installed
.venv/.installed:
	python3 -mvenv .venv
	.venv/bin/pip install -U wheel pip build twine black
	touch $@

format: venv
	.venv/bin/python3 -m black src/

build: venv
	.venv/bin/python3 -m build

release: clean build
	.venv/bin/python3 -m twine upload dist/*

clean:
	rm -rf .venv/ dist/ src/*.egg-info

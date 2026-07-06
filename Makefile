.PHONY: clean build release format

format:
	uvx black src/

build:
	uv build

release: clean build
	uv publish

clean:
	rm -rf dist/ src/*.egg-info

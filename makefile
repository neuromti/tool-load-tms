SHELL := /bin/bash

.PHONY: clean test build
.ONESHELL:


clean:
	rm -rf dist */*.egg-info *.egg-info  build
	rm -rf .env

build: clean
	python setup.py sdist bdist_wheel

test: build
	tests/run_tests




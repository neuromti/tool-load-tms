SHELL := /bin/bash

.PHONY: clean test
.ONESHELL:

test:
	tests/run_tests



.PHONY: clean
clean:
	rm -rf .env
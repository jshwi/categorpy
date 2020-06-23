CYAN	:= $(shell tput setaf 6)
RESET 	:= $(shell tput sgr0)
REPO 	:= $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
SETUP 	:= $(REPO)/setup.py
BIN 	:= $(REPO)/bin
LIB 	:= $(BIN)/lib.sh
WHICH	:= $(BIN)/which
BUILD	:= $(BIN)/build
BASH	:= /bin/bash
PYTHON	:= /bin/python3
NAME	:= $(shell $(PYTHON) $(SETUP) --name)
VERSION := $(shell $(PYTHON) $(SETUP) --version)


.PHONY: help
help:  ## Show this help message and exit
	@echo "$(CYAN)$(BOLD)$(NAME) v$(VERSION)$(RESET)"
	@echo "$(CYAN).$(RESET) usage:         make [TARGET]"
	@echo "$(CYAN).$(RESET) requirements:  make,python3.8,pipenv"
	@echo "$(CYAN)----------------------------------------------------$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk \
	'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'


.PHONY: which
which:  ## Check that pipenv is installed
	@$(BASH) -c "$(WHICH)"


.PHONY: install
install: which  ## Install bin executable
	@$(BASH) -c "source $(LIB); install_binary"


.PHONY: docs
docs: which  ## Compile documentation
	@$(BASH) -c "source $(LIB); make_html"


.PHONY: tests
tests: which  ## Run unittests
	@$(BASH) -c "source $(LIB); run_tests"


.PHONY: clean
clean:  ## Remove all untracked dirs and files
	@$(BASH) -c "source $(LIB) --no-install; clean_repo"


.PHONY: uninstall
uninstall: which  ## Uninstall binary
	@$(BASH) -c "source $(LIB) --no-install; uninstall"


.PHONY: format
format: which  ## Format all .py project files
	@$(BASH) -c "source $(LIB); format_py"


.PHONY: lint
lint: which  ## Show possible .py file corrections
	@$(BASH) -c "source $(LIB); lint_files"


.PHONY: coverage
coverage: which  ## Run unittests with coverage
	@$(BASH) -c "source $(LIB); run_test_cov"


.PHONY: typecheck
typecheck: which  ## Inspect files for type errors
	@$(BASH) -c "source $(LIB); inspect_types"


.PHONY: unused
unused: which  ## Inspect files for unused attributes
	@$(BASH) -c "source $(LIB); vulture"


.PHONY: whitelist
whitelist: which  ## Update whitelist.py
	@$(BASH) -c "source $(LIB); whitelist"


.PHONY: toc
toc: which  ## Update docs/<PACKAGENAME>.rst
	@$(BASH) -c "source $(LIB); make_toc"


.PHONY: requirements
requirements: which  ## Pipfile.lock -> requirements.txt
	@$(BASH) -c "source $(LIB); pipfile_to_requirements"


.PHONY: build
build: which  ## Run all checks, install and deploy
	@$(BASH) -c "source $(BUILD); do_build"

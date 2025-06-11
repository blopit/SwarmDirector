# SwarmDirector Makefile
# Development and testing commands

.PHONY: help test test-verbose test-coverage test-standalone test-single install-deps clean setup

# Default target
help:
	@echo "SwarmDirector Development Commands"
	@echo "=================================="
	@echo "test               - Run all tests"
	@echo "test-verbose       - Run tests with verbose output"
	@echo "test-coverage      - Run tests with coverage reporting"
	@echo "test-standalone    - Run only standalone test functions"
	@echo "test-single TEST=  - Run a specific test file"
	@echo "install-deps       - Install test dependencies"
	@echo "setup              - Set up development environment"
	@echo "clean              - Clean up generated files"

# Test targets
test:
	@python scripts/run_tests.py

test-verbose:
	@python scripts/run_tests.py -v

test-coverage:
	@python scripts/run_tests.py -c

test-standalone:
	@python scripts/run_tests.py -s

test-single:
	@python scripts/run_tests.py -t $(TEST)

# Development setup
install-deps:
	@python scripts/run_tests.py --install-deps
	@pip install -r requirements.txt

setup:
	@echo "Setting up SwarmDirector development environment..."
	@pip install -r requirements.txt
	@python scripts/run_tests.py --install-deps
	@echo "Setup complete! Run 'make test' to verify installation."

# Cleanup
clean:
	@echo "Cleaning up generated files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf reports/coverage 2>/dev/null || true
	@echo "Cleanup complete!"

# Clean test artifacts
clean-tests:
	@echo "Cleaning up test artifacts..."
	@rm -rf test_backups_* 2>/dev/null || true
	@rm -rf test_migrations_* 2>/dev/null || true
	@rm -rf pytest_backups_* 2>/dev/null || true
	@rm -rf pytest_migrations_* 2>/dev/null || true
	@find instance -name "*_test_*.db*" -delete 2>/dev/null || true
	@find . -name "*_pytest_*.db*" -delete 2>/dev/null || true
	@echo "Test artifacts cleanup complete!"

# Full cleanup including test artifacts
clean-all: clean clean-tests
	@echo "Full cleanup complete!"
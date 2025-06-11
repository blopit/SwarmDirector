# Testing Guide for SwarmDirector

This document explains how to run tests in the SwarmDirector project.

## Quick Start

The easiest way to run all tests is using one of these methods:

```bash
# Using Make (recommended)
make test

# Using Python script directly
python scripts/run_tests.py

# Using shell script
./scripts/run_tests.sh
```

## Test Runner Options

The `scripts/run_tests.py` script provides several options:

### Basic Usage
```bash
# Run all tests (default)
python scripts/run_tests.py

# Verbose output
python scripts/run_tests.py -v
python scripts/run_tests.py --verbose

# Run with coverage reporting
python scripts/run_tests.py -c
python scripts/run_tests.py --coverage
```

### Specific Test Types
```bash
# Run only pytest tests
python scripts/run_tests.py -p
python scripts/run_tests.py --pytest-only

# Run only standalone test functions
python scripts/run_tests.py -s
python scripts/run_tests.py --standalone

# Run a specific test file
python scripts/run_tests.py -t test_app.py
python scripts/run_tests.py --test test_app.py
```

### Dependencies
```bash
# Install missing test dependencies
python scripts/run_tests.py --install-deps
```

## Make Targets

The project includes a Makefile with convenient test targets:

```bash
# Show all available commands
make help

# Run all tests
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage reporting
make test-coverage

# Run only standalone test functions
make test-standalone

# Run a specific test file
make test-single TEST=test_app.py

# Install test dependencies
make install-deps

# Set up development environment
make setup

# Clean up generated files
make clean
```

## Test Structure

The project uses a hybrid testing approach:

### 1. pytest Tests
- Modern test framework with automatic test discovery
- Located in `tests/` directory
- Run with: `pytest tests/`
- Supports fixtures, parameterization, and plugins

### 2. Standalone Test Functions
- Legacy test functions for backwards compatibility
- Some test files have `run_tests()` functions
- Useful for integration testing and custom test logic

## Coverage Reporting

When running tests with coverage (`-c` or `--coverage`):
- Terminal output shows line coverage percentages
- HTML report generated in `reports/coverage/`
- Open `reports/coverage/index.html` in browser for detailed view

## Test Files

Current test files in the project:

- `test_app.py` - Flask application tests
- `test_database_utils.py` - Database utility tests  
- `test_director_agent.py` - Director agent tests
- `test_relationships.py` - Data relationship tests
- `test_advanced_relationships.py` - Advanced relationship tests

## Dependencies

Required testing packages (automatically installed):
- `pytest` - Main testing framework
- `pytest-cov` - Coverage reporting plugin

These are included in `requirements.txt` and can be installed with:
```bash
pip install -r requirements.txt
```

## Continuous Integration

The test runner returns appropriate exit codes:
- `0` - All tests passed
- `1` - Some tests failed

This makes it suitable for CI/CD pipelines:
```bash
# In CI/CD scripts
python scripts/run_tests.py || exit 1
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**: Ensure you're running from project root
2. **pytest not found**: Run with `--install-deps` flag
3. **Database errors**: Check database configuration and permissions
4. **Import errors**: Verify virtual environment is activated

### Debug Mode

For debugging test failures:
```bash
# Run with maximum verbosity
python scripts/run_tests.py -v

# Run specific failing test
python scripts/run_tests.py -t failing_test.py

# Run standalone tests only (sometimes more detailed output)
python scripts/run_tests.py -s
```

## Contributing

When adding new tests:

1. Create test files in `tests/` directory
2. Use `test_` prefix for files and functions
3. Include both pytest-style and standalone `run_tests()` if needed
4. Update this documentation if new test categories are added
5. Ensure tests pass before submitting PRs

## Examples

### Running Tests in Development
```bash
# Quick test run during development
make test

# Detailed testing before commit
make test-coverage

# Test specific component
make test-single TEST=test_app.py
```

### CI/CD Integration
```bash
#!/bin/bash
# In CI/CD pipeline
set -e
python scripts/run_tests.py --coverage
# Upload coverage reports to service if needed
``` 
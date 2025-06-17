# SwarmDirector Makefile
# Development and testing commands

.PHONY: help test test-verbose test-coverage test-standalone test-single install-deps clean setup task-trigger

# Task Management Integration
TASK_INTEGRATION_SCRIPT := python -c "import sys; sys.path.insert(0, 'src'); \
	try: \
		from swarm_director.utils.automation import trigger_task_automation, AutomationEventType; \
		trigger_task_automation(AutomationEventType.$(EVENT_TYPE), '$(TASK_ID)', $(METADATA)); \
		print('✅ Task event triggered: $(EVENT_TYPE)'); \
	except Exception as e: \
		print('⚠️  Task integration not available:', e);"

# Helper targets for task management
task-start:
	@$(call task-event,TASK_STARTED,makefile_$(TARGET),'{"target":"$(TARGET)","timestamp":"$(shell date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"}')

task-complete:
	@$(call task-event,TASK_COMPLETED,makefile_$(TARGET),'{"target":"$(TARGET)","success":true,"timestamp":"$(shell date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"}')

task-fail:
	@$(call task-event,TASK_FAILED,makefile_$(TARGET),'{"target":"$(TARGET)","success":false,"timestamp":"$(shell date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"}')

define task-event
	@EVENT_TYPE=$(1) TASK_ID=$(2) METADATA=$(3) $(TASK_INTEGRATION_SCRIPT)
endef

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

# Test targets with task integration
test:
	@$(call task-event,TASK_STARTED,make_test,'{"action":"test","type":"all"}')
	@python scripts/run_tests.py && \
		$(call task-event,TASK_COMPLETED,make_test,'{"action":"test","success":true}') || \
		($(call task-event,TASK_FAILED,make_test,'{"action":"test","success":false}') && exit 1)

test-verbose:
	@$(call task-event,TASK_STARTED,make_test_verbose,'{"action":"test","type":"verbose"}')
	@python scripts/run_tests.py -v && \
		$(call task-event,TASK_COMPLETED,make_test_verbose,'{"action":"test","success":true}') || \
		($(call task-event,TASK_FAILED,make_test_verbose,'{"action":"test","success":false}') && exit 1)

test-coverage:
	@$(call task-event,TASK_STARTED,make_test_coverage,'{"action":"test","type":"coverage"}')
	@python scripts/run_tests.py -c && \
		$(call task-event,TASK_COMPLETED,make_test_coverage,'{"action":"test","success":true}') || \
		($(call task-event,TASK_FAILED,make_test_coverage,'{"action":"test","success":false}') && exit 1)

test-standalone:
	@$(call task-event,TASK_STARTED,make_test_standalone,'{"action":"test","type":"standalone"}')
	@python scripts/run_tests.py -s && \
		$(call task-event,TASK_COMPLETED,make_test_standalone,'{"action":"test","success":true}') || \
		($(call task-event,TASK_FAILED,make_test_standalone,'{"action":"test","success":false}') && exit 1)

test-single:
	@$(call task-event,TASK_STARTED,make_test_single,'{"action":"test","type":"single","target":"$(TEST)"}')
	@python scripts/run_tests.py -t $(TEST) && \
		$(call task-event,TASK_COMPLETED,make_test_single,'{"action":"test","success":true}') || \
		($(call task-event,TASK_FAILED,make_test_single,'{"action":"test","success":false}') && exit 1)

# Development setup with task integration
install-deps:
	@$(call task-event,BUILD_STARTED,make_install_deps,'{"action":"install_dependencies"}')
	@python scripts/run_tests.py --install-deps && pip install -r requirements.txt && \
		$(call task-event,BUILD_COMPLETED,make_install_deps,'{"action":"install_dependencies","success":true}') || \
		($(call task-event,BUILD_FAILED,make_install_deps,'{"action":"install_dependencies","success":false}') && exit 1)

setup:
	@echo "Setting up SwarmDirector development environment..."
	@$(call task-event,DEPLOYMENT_STARTED,make_setup,'{"action":"development_setup"}')
	@pip install -r requirements.txt && \
	 python scripts/run_tests.py --install-deps && \
	 python scripts/setup_development.py && \
	 echo "Setup complete! Run 'make test' to verify installation." && \
		$(call task-event,DEPLOYMENT_COMPLETED,make_setup,'{"action":"development_setup","success":true}') || \
		($(call task-event,DEPLOYMENT_FAILED,make_setup,'{"action":"development_setup","success":false}') && exit 1)

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
.PHONY: test lint format install clean

# Variables
PYTHON := python3
PIP := pip
PYTEST := pytest
FLAKE8 := flake8
BLACK := black
PROJECT := src tests

# Color codes
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Define the default target when `make` is run without arguments
.DEFAULT_GOAL := help

# Help target
help:
	@echo "${BLUE}Automate Meroshare IPO${NC} - Development Commands"
	@echo ""
	@echo "${YELLOW}Usage:${NC}"
	@echo "  make ${GREEN}<command>${NC}"
	@echo ""
	@echo "${YELLOW}Commands:${NC}"
	@echo "  ${GREEN}install${NC}      Install project dependencies"
	@echo "  ${GREEN}test${NC}         Run tests"
	@echo "  ${GREEN}lint${NC}         Check code style with flake8"
	@echo "  ${GREEN}format${NC}       Format code with black"
	@echo "  ${GREEN}clean${NC}        Remove cached files and directories"
	@echo "  ${GREEN}help${NC}         Show this help message"

# Install dependencies
install:
	@echo "${BLUE}Installing dependencies...${NC}"
	$(PIP) install -r requirements.txt
	@echo "${GREEN}Dependencies installed successfully!${NC}"

# Run tests
test:
	@echo "${BLUE}Running tests...${NC}"
	$(PYTEST) -v

# Run linting
lint:
	@echo "${BLUE}Checking code style with flake8...${NC}"
	$(FLAKE8) $(PROJECT)

# Format code
format:
	@echo "${BLUE}Formatting code with black...${NC}"
	$(BLACK) $(PROJECT)

# Clean cache files
clean:
	@echo "${BLUE}Cleaning up...${NC}"
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type f -name "coverage.xml" -delete
	find . -type f -name ".DS_Store" -delete
	@echo "${GREEN}Cleanup complete!${NC}"

# Run all checks
check: lint test
	@echo "${GREEN}All checks passed!${NC}"

# Create and activate virtual environment (helper function)
venv:
	@echo "${BLUE}Creating virtual environment...${NC}"
	$(PYTHON) -m venv venv
	@echo "${GREEN}Virtual environment created!${NC}"
	@echo ""
	@echo "${YELLOW}To activate, run:${NC}"
	@echo "  source venv/bin/activate"


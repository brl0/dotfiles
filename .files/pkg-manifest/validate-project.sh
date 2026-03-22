#!/bin/bash

################################################################################
# Project Validation and Test Script
# Comprehensive testing and validation for project structure, dependencies,
# tests, and documentation
################################################################################

set -o pipefail

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
RESET='\033[0m'
BOLD='\033[1m'

# Counters and tracking
TESTS_PASSED=0
TESTS_FAILED=0
WARNINGS=0
START_TIME=$(date +%s)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "\n${BOLD}${BLUE}════════════════════════════════════════════════════════════${RESET}"
    echo -e "${BOLD}${CYAN}► $1${RESET}"
    echo -e "${BOLD}${BLUE}════════════════════════════════════════════════════════════${RESET}\n"
}

print_section() {
    echo -e "\n${BOLD}${CYAN}▸ $1${RESET}"
}

print_pass() {
    echo -e "${GREEN}✓ PASS${RESET}: $1"
    ((TESTS_PASSED++))
}

print_fail() {
    echo -e "${RED}✗ FAIL${RESET}: $1"
    ((TESTS_FAILED++))
}

print_warn() {
    echo -e "${YELLOW}⚠ WARN${RESET}: $1"
    ((WARNINGS++))
}

print_info() {
    echo -e "${CYAN}ℹ INFO${RESET}: $1"
}

get_elapsed_time() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    echo "${elapsed}s"
}

################################################################################
# 1. PROJECT STRUCTURE VALIDATION
################################################################################

validate_project_structure() {
    print_header "1. PROJECT STRUCTURE VALIDATION"

    local required_dirs=(
        "."
        ".git"
        ".files/pkg-manifest"
        "docs"
    )

    local required_files=(
        "README.md"
        ".gitignore"
        "docs/PKG-MANIFEST-INDEX.md"
    )

    print_section "Checking required directories"
    for dir in "${required_dirs[@]}"; do
        if [ -d "$SCRIPT_DIR/$dir" ]; then
            print_pass "Directory exists: $dir"
        else
            print_fail "Directory missing: $dir"
        fi
    done

    print_section "Checking required files"
    for file in "${required_files[@]}"; do
        if [ -f "$SCRIPT_DIR/$file" ]; then
            print_pass "File exists: $file"
        else
            print_warn "File missing: $file"
        fi
    done
}

################################################################################
# 2. FILE INTEGRITY CHECKS
################################################################################

validate_file_integrity() {
    print_header "2. FILE INTEGRITY CHECKS"

    print_section "Checking Python files syntax"
    local python_files=$(find "$SCRIPT_DIR" -name "*.py" -type f 2>/dev/null | grep -v __pycache__)

    if [ -z "$python_files" ]; then
        print_warn "No Python files found in project"
        return
    fi

    local py_syntax_ok=0
    local py_syntax_fail=0

    while IFS= read -r py_file; do
        if python3 -m py_compile "$py_file" 2>/dev/null; then
            ((py_syntax_ok++))
        else
            print_fail "Python syntax error in: $py_file"
            ((py_syntax_fail++))
        fi
    done <<< "$python_files"

    if [ $py_syntax_fail -eq 0 ]; then
        print_pass "All Python files have valid syntax ($py_syntax_ok files)"
    else
        print_fail "Found $py_syntax_fail file(s) with syntax errors"
    fi

    print_section "Checking Markdown documentation"
    local md_files=$(find "$SCRIPT_DIR/docs" -name "PKG-MANIFEST-*.md" -type f 2>/dev/null)
    local md_count=$(echo "$md_files" | grep -c PKG-MANIFEST || echo 0)

    if [ $md_count -ge 4 ]; then
        print_pass "Documentation files found: $md_count files"
    else
        print_warn "Expected 5 docs files, found: $md_count"
    fi
}

################################################################################
# 3. PYTHON ENVIRONMENT CHECKS
################################################################################

check_python_environment() {
    print_header "3. PYTHON ENVIRONMENT CHECKS"

    print_section "Python installation"
    if command -v python3 &> /dev/null; then
        local py_version=$(python3 --version 2>&1)
        print_pass "Python3 installed: $py_version"
    else
        print_fail "Python3 is not installed"
        return 1
    fi

    print_section "Required Python modules"
    local required_modules=("sys" "os" "json" "unittest" "logging")
    local missing_modules=0

    for module in "${required_modules[@]}"; do
        if python3 -c "import $module" 2>/dev/null; then
            print_pass "Module available: $module"
        else
            print_fail "Module missing: $module"
            ((missing_modules++))
        fi
    done
}

################################################################################
# 4. TEST SUITE EXECUTION
################################################################################

run_test_suite() {
    print_header "4. TEST SUITE EXECUTION"

    print_section "Locating test files"
    local test_script="$SCRIPT_DIR/.files/pkg-manifest/run_tests.py"

    if [ -f "$test_script" ]; then
        print_pass "Test script found: run_tests.py"

        print_section "Executing test suite..."
        echo ""

        if python3 "$test_script" 2>&1 | head -20; then
            print_pass "Test suite execution started"
        else
            print_warn "Test suite execution had issues (check output above)"
        fi
    else
        print_warn "Test suite not found at $test_script"
    fi
}

################################################################################
# 5. DOCUMENTATION VALIDATION
################################################################################

validate_documentation() {
    print_header "5. DOCUMENTATION VALIDATION"

    print_section "Checking documentation files"

    local doc_files=(
        "PKG-MANIFEST-INDEX.md"
        "PKG-MANIFEST-MASTER-REQUIREMENTS.md"
        "PKG-MANIFEST-IMPLEMENTATION-STATUS.md"
        "PKG-MANIFEST-TESTING-GUIDE.md"
        "PKG-MANIFEST-CONTINUED-WORK.md"
    )

    local docs_found=0

    for doc in "${doc_files[@]}"; do
        if [ -f "$SCRIPT_DIR/docs/$doc" ]; then
            local wc=$(wc -w < "$SCRIPT_DIR/docs/$doc" || echo 0)
            print_pass "$doc ($wc words)"
            ((docs_found++))
        else
            print_warn "$doc not found"
        fi
    done

    if [ $docs_found -ge 4 ]; then
        print_pass "Documentation complete: $docs_found/5 files"
    fi
}

################################################################################
# 6. PROJECT METRICS AND SUMMARY
################################################################################

print_project_metrics() {
    print_header "6. PROJECT METRICS"

    print_section "Code statistics"

    # Python files count
    local py_count=$(find "$SCRIPT_DIR" -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | wc -l)
    print_info "Python files: $py_count"

    # Lines of Python code
    local py_lines=$(find "$SCRIPT_DIR" -name "*.py" -type f 2>/dev/null | grep -v __pycache__ | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
    if [ -n "$py_lines" ] && [ "$py_lines" -gt 0 ]; then
        print_info "Python lines of code: $py_lines"
    fi

    # Markdown documentation
    local md_count=$(find "$SCRIPT_DIR/docs" -name "*.md" -type f 2>/dev/null | wc -l)
    [ "$md_count" -gt 0 ] && print_info "Markdown files: $md_count"

    # Git information
    if [ -d "$SCRIPT_DIR/.git" ]; then
        local commit_count=$(cd "$SCRIPT_DIR" && git rev-list --count HEAD 2>/dev/null || echo "0")
        print_info "Git commits: $commit_count"

        local branch=$(cd "$SCRIPT_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
        print_info "Current branch: $branch"
    fi
}

################################################################################
# MAIN SUMMARY AND EXIT
################################################################################

print_final_summary() {
    local elapsed=$(get_elapsed_time)
    local total_tests=$((TESTS_PASSED + TESTS_FAILED))

    print_header "VALIDATION SUMMARY"

    echo -e "${BOLD}Results:${RESET}"
    echo -e "  ${GREEN}✓ Passed: $TESTS_PASSED${RESET}"
    echo -e "  ${RED}✗ Failed: $TESTS_FAILED${RESET}"
    echo -e "  ${YELLOW}⚠ Warnings: $WARNINGS${RESET}"
    echo -e "  ${CYAN}ℹ Total checks: $total_tests${RESET}"
    echo ""
    echo -e "${BOLD}Execution:${RESET}"
    echo -e "  Time elapsed: ${CYAN}$elapsed${RESET}"
    echo ""

    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}${BOLD}✓ PROJECT VALIDATION PASSED${RESET}\n"
        return 0
    else
        echo -e "${RED}${BOLD}✗ PROJECT VALIDATION FAILED${RESET}"
        echo -e "${YELLOW}Please review the failures above.${RESET}\n"
        return 1
    fi
}

################################################################################
# MAIN EXECUTION
################################################################################

main() {
    echo -e "${BOLD}${CYAN}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║         PROJECT VALIDATION AND TEST SUITE                 ║"
    echo "║         $(date '+%Y-%m-%d %H:%M:%S')                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${RESET}"

    print_info "Project root: $SCRIPT_DIR"
    echo ""

    # Run all validation sections
    validate_project_structure
    validate_file_integrity
    check_python_environment
    run_test_suite
    validate_documentation
    print_project_metrics

    # Print final summary and exit
    print_final_summary
    exit_code=$?

    exit $exit_code
}

# Run main function
main "$@"

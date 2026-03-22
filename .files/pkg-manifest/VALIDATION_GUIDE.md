# Project Validation Script Guide

## Overview

The `validate-project.sh` script provides comprehensive testing and validation for the pkg-manifest project.

## Quick Start

```bash
cd /home/brl0/dotfiles
chmod +x .files/pkg-manifest/validate-project.sh
.files/pkg-manifest/validate-project.sh
```

## What It Validates

1. **Project Structure** - Required directories and files
2. **File Integrity** - Python syntax and Markdown files
3. **Python Environment** - Python version and required modules
4. **Test Suite** - Runs existing tests if available
5. **Documentation** - Verifies documentation files
6. **Project Metrics** - Code statistics and git information

## Output Features

- **Color-Coded Results**: Green (✓), Red (✗), Yellow (⚠), Cyan (ℹ)
- **Summary Report**: Pass/fail counts, execution time
- **Proper Exit Codes**: 0 for success, 1 for failure

## Usage

### Basic Usage

```bash
.files/pkg-manifest/validate-project.sh
```

### Check Exit Code

```bash
.files/pkg-manifest/validate-project.sh
echo "Exit code: $?"
```

### Save Output to File

```bash
.files/pkg-manifest/validate-project.sh > validation_report.txt 2>&1
```

## Integration

For CI/CD pipelines:

```bash
.files/pkg-manifest/validate-project.sh || exit 1
```

## See Also

- [PKG-MANIFEST-TESTING-GUIDE.md](../../docs/PKG-MANIFEST-TESTING-GUIDE.md) - Detailed test procedures
- [PKG-MANIFEST-INDEX.md](../../docs/PKG-MANIFEST-INDEX.md) - Documentation index

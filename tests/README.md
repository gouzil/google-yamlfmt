# Test Configuration for yamlfmt

This directory contains tests for the yamlfmt cross-platform functionality.

## Test Files

- `test_yamlfmt.py`: Main test suite that validates yamlfmt functionality across different platforms

## Running Tests

### Local Testing

Run tests locally with:

```bash
python -m pytest tests/ -v
```

Or run the test script directly:

```bash
python tests/test_yamlfmt.py
```

### CI Testing

The tests are automatically run in GitHub Actions across multiple platforms:

- Linux (Ubuntu)
- macOS
- Windows

## Test Coverage

The test suite covers:

1. **Platform Detection**: Verifies the current platform can be detected
2. **Version Output**: Tests that yamlfmt can output version information
3. **Basic Formatting**: Tests basic YAML formatting functionality
4. **Executable Permissions**: Verifies the yamlfmt executable has correct permissions
5. **Help Output**: Tests that yamlfmt can show help information
6. **Module Import**: Tests that the yamlfmt module can be imported correctly
7. **System Information**: Displays system information for debugging

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention (`test_*`)
2. Include appropriate error handling for cross-platform compatibility
3. Add descriptive docstrings
4. Use appropriate assertions for validation
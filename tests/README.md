# NetHang Tests

This directory contains comprehensive tests for the NetHang application.

## Test Structure

- `test_config_manager.py` - Tests for the ConfigManager class
- `test_about.py` - Test for the About page
- `conftest.py` - Shared fixtures and test configuration
- `__init__.py` - Makes tests a Python package

## Running Tests

### Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_config_manager.py
```

### Run Tests with Coverage

```bash
pytest --cov=nethang --cov-report=html
```

### Run Tests in Parallel

```bash
pytest -n auto
```

### Run Tests with Verbose Output

```bash
pytest -v
```

## Test Categories

The tests are organized into the following categories:

### Unit Tests
- Test individual methods and functions in isolation
- Use mocking to isolate dependencies
- Fast execution

### Integration Tests
- Test interactions between components
- May use real file system or network calls
- Slower execution

### Network Tests
- Tests that require network access
- Marked with `@pytest.mark.network`

### Slow Tests
- Tests that take longer to execute
- Marked with `@pytest.mark.slow`

## Test Coverage

The tests cover:

### ConfigManager Class
- Initialization and configuration
- GitHub config download functionality
- Fallback config creation
- Config file validation
- Error handling for network issues
- YAML parsing and validation
- File operations (create, read, update)
- Backup and restore functionality

### Key Test Scenarios
- Successful config download from GitHub
- Network failure handling
- Invalid YAML content handling
- File system errors
- Config update logic
- Fallback mechanism activation

## Mocking Strategy

The tests use extensive mocking to:

- Isolate the unit under test
- Avoid real network calls
- Control file system operations
- Simulate error conditions
- Test edge cases

## Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_test_dir` - Temporary directory for test files
- `mock_flask_app` - Mock Flask application
- `mock_config_paths` - Mock configuration paths
- `sample_yaml_config` - Sample YAML configuration
- `mock_github_response_success` - Mock successful GitHub response
- `mock_requests_get_success` - Mock successful HTTP requests
- `mock_file_operations` - Mock file operations

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Use mocks to isolate dependencies
3. **Cleanup**: Clean up resources after tests
4. **Descriptive Names**: Use clear, descriptive test names
5. **Documentation**: Document complex test scenarios
6. **Edge Cases**: Test error conditions and edge cases
7. **Coverage**: Aim for high test coverage

## Adding New Tests

When adding new tests:

1. Follow the existing naming convention
2. Use appropriate fixtures from `conftest.py`
3. Mock external dependencies
4. Test both success and failure scenarios
5. Add appropriate markers for test categorization
6. Update this README if adding new test categories
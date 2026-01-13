# API Connection Testing Guide

This directory contains test suites for verifying the Anthropic Claude API connection and integration with the Research Orchestrator system.

## Test Files

### 1. `test_api_connection.py` - Standalone Test Script

A self-contained script for quick API connection verification. Can be run directly without pytest.

**Purpose:**
- Verify API key is configured correctly
- Test basic client initialization
- Confirm model availability
- Validate token tracking and cost estimation
- Test error handling

**How to Run:**
```bash
# From the src directory
cd src

# Make sure ANTHROPIC_API_KEY is set in your .env file
# Then run:
python tests/test_api_connection.py
```

**What It Tests:**
1. **API Key Configuration** - Verifies the key exists and has correct format
2. **Client Initialization** - Tests AsyncAnthropic client creation
3. **Simple Message Exchange** - Sends a basic message and validates response
4. **Model Availability** - Confirms claude-sonnet-4-20250514 is accessible
5. **Token Tracking** - Verifies token usage is tracked correctly
6. **Error Handling** - Tests that invalid requests fail appropriately

**Expected Output:**
```
======================================================================
Anthropic API Connection Test Suite
Started: 2025-10-09 12:30:00
======================================================================

=== Test 1: API Key Configuration ===
✓ PASS: API Key Present - Key found: sk-ant-...ESg

=== Test 2: Client Initialization ===
✓ PASS: Client Initialization - AsyncAnthropic client created successfully

=== Test 3: Simple Message Exchange ===
Sending test message to Claude...
✓ PASS: Simple Message - Received response (34 chars): API connection test successful
  Input tokens: 20
  Output tokens: 12

=== Test 4: Model Availability ===
Testing model: claude-sonnet-4-20250514
✓ PASS: Model Availability - Model claude-sonnet-4-20250514 is accessible

=== Test 5: Token Usage Tracking ===
✓ PASS: Token Tracking - Tracked 65 tokens ($0.000705)
  Input: 26 tokens ($0.000078)
  Output: 39 tokens ($0.000585)

=== Test 6: Error Handling ===
✓ PASS: Error Handling - Correctly caught NotFoundError for invalid model

======================================================================
TEST SUMMARY
======================================================================
✓ API Key Present
✓ Client Initialization
✓ Simple Message
✓ Model Availability
✓ Token Tracking
✓ Error Handling
======================================================================
Results: 6/6 tests passed
✓ ALL TESTS PASSED - API connection is working correctly
======================================================================
```

### 2. `test_research_session.py` - Pytest Test Suite

Comprehensive pytest test suite for the ResearchSession class with both unit tests and integration tests.

**Purpose:**
- Unit test ResearchSession initialization and methods
- Integration test real API interactions
- Verify retry logic and error handling
- Test token tracking and cost estimation
- Validate research execution workflow

**How to Run:**

```bash
# From the src directory
cd src

# Install pytest if not already installed
pip install pytest pytest-asyncio

# Run all tests
pytest tests/test_research_session.py -v

# Run only unit tests (no API calls)
pytest tests/test_research_session.py -v -m "not integration"

# Run only integration tests (makes API calls)
pytest tests/test_research_session.py -v -m integration

# Run with detailed output
pytest tests/test_research_session.py -v -s
```

**Test Categories:**

#### Unit Tests (No API Calls)
- `TestResearchSessionInitialization` - Tests object creation
- `TestResearchSessionTokenTracking` - Tests cost calculation
- `TestResearchSessionContentExtraction` - Tests text parsing
- `TestResearchSessionRetryLogic` - Tests error retry logic

#### Integration Tests (Makes API Calls)
- `TestResearchSessionIntegration` - Tests real API interactions
  - Simple research execution
  - Web search functionality
  - Max turns enforcement
  - Session summary generation

**Cost Considerations:**

Integration tests make real API calls and will incur costs:
- Simple test: ~$0.001 (1,000 tokens)
- Web search test: ~$0.01-0.02 (10,000-20,000 tokens)
- Total for full suite: ~$0.05-0.10

To skip integration tests and avoid API costs:
```bash
pytest tests/test_research_session.py -v -m "not integration"
```

## Prerequisites

### 1. Environment Setup

Ensure your `.env` file in the `src` directory contains your API key:

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### 2. Python Dependencies

Install required packages:

```bash
# From the project root
cd src
pip install -r requirements.txt

# Additional test dependencies
pip install pytest pytest-asyncio
```

## Quick Start Testing Guide

### Step 1: Verify API Key Setup

```bash
cd src
python tests/test_api_connection.py
```

If this fails:
1. Check that `.env` file exists in `src/` directory
2. Verify `ANTHROPIC_API_KEY` is set correctly
3. Ensure the key starts with `sk-ant-`
4. Test the key directly at https://console.anthropic.com

### Step 2: Run Unit Tests (Free - No API Calls)

```bash
cd src
pytest tests/test_research_session.py -v -m "not integration"
```

This verifies your code is structured correctly without making API calls.

### Step 3: Run Integration Tests (Small Cost)

```bash
cd src
pytest tests/test_research_session.py -v -m integration -s
```

This makes real API calls to verify end-to-end functionality. Expected cost: ~$0.05-0.10

## Troubleshooting

### Error: "ANTHROPIC_API_KEY not found in environment"

**Solution:**
1. Create or check `src/.env` file
2. Add line: `ANTHROPIC_API_KEY=your-key-here`
3. Ensure no quotes around the key value
4. Restart your terminal/IDE to reload environment

### Error: "Module 'anthropic' not found"

**Solution:**
```bash
cd src
pip install anthropic
```

### Error: "Module 'pytest' not found"

**Solution:**
```bash
pip install pytest pytest-asyncio
```

### Error: "AuthenticationError: Invalid API key"

**Solution:**
1. Verify your API key at https://console.anthropic.com
2. Generate a new key if needed
3. Update your `.env` file
4. Ensure no extra spaces or characters in the key

### Error: "RateLimitError"

**Solution:**
- Wait a few seconds and try again
- The retry logic should handle this automatically
- If persistent, check your API usage limits at console.anthropic.com

### Tests are very slow

**Possible Causes:**
1. Network latency - API calls to Anthropic servers
2. Rate limiting - API may be throttling requests
3. Complex prompts - Longer prompts = longer processing

**Solutions:**
- Run unit tests only (no API calls): `pytest -m "not integration"`
- Reduce max_tokens in integration tests
- Check your network connection

## Continuous Integration

To add these tests to CI/CD:

```yaml
# Example GitHub Actions workflow
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd src
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      
      - name: Run unit tests
        run: |
          cd src
          pytest tests/ -v -m "not integration"
      
      - name: Run integration tests
        if: github.event_name == 'push'
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          cd src
          pytest tests/ -v -m integration
```

## Best Practices

1. **Run standalone test first** - Quick verification before deeper testing
2. **Use unit tests during development** - Fast feedback without API costs
3. **Run integration tests before deployment** - Ensure real API works
4. **Monitor API costs** - Integration tests cost ~$0.05-0.10 per run
5. **Keep API key secure** - Never commit `.env` file to version control

## Test Coverage

Current test coverage:

- ✅ API key validation
- ✅ Client initialization
- ✅ Basic message exchange
- ✅ Model availability
- ✅ Token usage tracking
- ✅ Cost estimation
- ✅ Error handling
- ✅ Retry logic
- ✅ Content extraction
- ✅ Web search integration
- ✅ Session management
- ✅ Max turns enforcement

## Next Steps

After verifying API connection:

1. **Test Full Orchestrator** - Run `python run_research.py` with a test config
2. **Monitor Costs** - Check actual vs estimated costs at console.anthropic.com
3. **Review Logs** - Check `src/logs/` for execution details
4. **Validate Outputs** - Review generated research in `src/outputs/`

## Support

For issues or questions:
1. Check the main project README.md
2. Review the HANDOFF.md document
3. Check logs in `src/logs/` directory
4. Verify API status at https://status.anthropic.com

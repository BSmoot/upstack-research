# Quick Start: Testing Your LLM API Connection

**⏱️ 2 Minute Quick Test**

## Step 1: Verify Your Setup (30 seconds)

Check that your API key is configured:

```bash
cd src
cat .env | grep ANTHROPIC_API_KEY
```

You should see: `ANTHROPIC_API_KEY=sk-ant-...`

If not, add it to your `.env` file.

## Step 2: Run the Connection Test (90 seconds)

```bash
python tests/test_api_connection.py
```

### ✅ Success Looks Like This:

```
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

### ❌ Common Issues:

**"API Key not found"**
→ Add `ANTHROPIC_API_KEY=your-key-here` to `src/.env`

**"Authentication failed"**
→ Check your key at https://console.anthropic.com

**"Module not found"**
→ Run: `pip install -r requirements.txt`

## What This Tests

| Test | What It Verifies | Cost |
|------|-----------------|------|
| API Key Present | Key is configured correctly | Free |
| Client Init | Can connect to Anthropic | Free |
| Simple Message | Can send/receive messages | ~$0.0001 |
| Model Availability | Your model is accessible | ~$0.0001 |
| Token Tracking | Usage tracking works | ~$0.0002 |
| Error Handling | Errors are handled correctly | Free |

**Total Cost: ~$0.0004 (less than 1 cent)**

## Next Steps

### ✅ If All Tests Pass:

Your API connection is working! You can now:

1. **Run the full system**: `python run_research.py`
2. **Run integration tests**: `pytest tests/test_research_session.py -v -m integration`
3. **Start development**: Your API setup is confirmed

### ❌ If Tests Fail:

1. Check the error message
2. Review `src/tests/README.md` for detailed troubleshooting
3. Verify your API key at https://console.anthropic.com
4. Check API status at https://status.anthropic.com

## Files Created

This testing suite includes:

- `test_api_connection.py` - Standalone quick test (this one)
- `test_research_session.py` - Comprehensive pytest suite
- `README.md` - Detailed documentation and troubleshooting
- `QUICK_START.md` - This quick reference guide

## Cost Monitoring

Each test run costs approximately **$0.0004 (0.04 cents)**.

To monitor your actual costs:
1. Visit https://console.anthropic.com
2. Check your usage dashboard
3. Compare with the estimates shown in test output

## Support

- Full docs: `src/tests/README.md`
- Project README: `src/README.md`
- Handoff docs: `src/HANDOFF.md`

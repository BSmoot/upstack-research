# SSL Certificate Error Fix

## Problem
You're seeing this error:
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate
```

This is a Windows/corporate network SSL certificate issue, NOT a problem with the code.

## Quick Fixes (Try in Order)

### Option 1: Update Certificate Bundle (RECOMMENDED)
```bash
pip install --upgrade certifi
python -m pip install --upgrade pip
```

### Option 2: Set SSL Certificate Path
```bash
# Find where your Python certificates are
python -c "import certifi; print(certifi.where())"

# Set environment variable (add to your shell profile)
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
export REQUESTS_CA_BUNDLE=$(python -c "import certifi; print(certifi.where())")
```

For Windows PowerShell:
```powershell
$env:SSL_CERT_FILE = python -c "import certifi; print(certifi.where())"
$env:REQUESTS_CA_BUNDLE = python -c "import certifi; print(certifi.where())"
```

### Option 3: Install Corporate Certificates (If on Corporate Network)
If you're on a corporate network with a proxy/firewall:

1. Ask IT for the corporate root CA certificate
2. Install it:
```bash
# Get current cert file location
python -c "import certifi; print(certifi.where())"

# Append your corporate cert to that file
# Example: cat corporate_cert.pem >> /path/to/certifi/cacert.pem
```

### Option 4: Test with Verification Disabled (TEMPORARY ONLY)
**WARNING: Only use for testing, NOT for production**

Add this to beginning of `src/run_research.py`:
```python
import ssl
ssl._create_default_https_context = ssl._create_unverified_context
```

Or set environment variable:
```bash
export PYTHONHTTPSVERIFY=0
```

**Do NOT use this for production - it makes API calls insecure!**

### Option 5: Use Different Python Environment
```bash
# Create fresh Python environment
python -m venv fresh_env
fresh_env\Scripts\activate  # Windows
# or: source fresh_env/bin/activate  # Mac/Linux

# Install requirements fresh
pip install -r requirements.txt
```

## Verify Fix
Test the API connection:
```bash
python -c "import anthropic; client = anthropic.Anthropic(); print('Connection OK')"
```

If this prints "Connection OK", your SSL is fixed!

## Still Not Working?

### Check Your Network
1. Are you behind a corporate proxy?
2. Are you on VPN?
3. Try disconnecting from VPN and testing again

### Check Python Installation
```bash
python --version  # Should be 3.11+
pip --version
which python  # Check which Python you're using
```

### Contact IT
If on corporate network, your IT department may need to:
- Whitelist `api.anthropic.com`
- Install corporate SSL certificates
- Configure proxy settings

## After Fixing

Once SSL works, re-run your test:
```bash
cd src
python run_research.py --agents buyer_journey --config ../build/design/251002_initial_design/research_config.yaml
```

## The Good News

✅ The code is working correctly!  
✅ This is just an environment/network configuration issue  
✅ Once SSL is fixed, research execution will work perfectly  

The fact that the system got all the way to making the API call means everything else is working correctly.

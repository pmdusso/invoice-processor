# Security and Privacy Guide

## 🔐 Important Security Notice

This invoice processor handles sensitive financial documents. Please follow these security guidelines when using or contributing to this project.

## 🚨 What This Project Handles

- **PDF invoices** containing financial information
- **Company names and billing details**
- **Monetary amounts and transaction data**
- **API keys** for OpenAI services
- **Processing logs** with extracted invoice content

## 🛡️ Security Measures Implemented

### Data Protection
- **Environment variables** for API keys (never hardcoded)
- **Local provider mapping** to reduce API calls and costs
- **Configurable output folders** for controlled data storage
- **Comprehensive .gitignore** to prevent accidental data commits

### Access Control
- **No network access** except to OpenAI API
- **File system isolation** to input/output folders only
- **Error handling** prevents data leakage through exceptions
- **Logging controls** to avoid sensitive data in logs

## 📋 Privacy Best Practices for Users

### Before Using
1. **Never commit your `.env` file** to version control
2. **Use dedicated API keys** with limited permissions
3. **Process in isolated environments** when possible
4. **Review provider mappings** before sharing

### During Processing
1. **Secure your input/output folders** with appropriate permissions
2. **Use validation mode first** to check file integrity
3. **Monitor API usage** and costs
4. **Regular cleanup** of logs and temporary files

### After Processing
1. **Securely store processed invoices**
2. **Delete sensitive logs** when no longer needed
3. **Rotate API keys** periodically
4. **Backup provider mappings** separately

## 🔒 Open Source Considerations

### What's Safe to Share
- ✅ Source code (all `.py` files)
- ✅ Documentation and examples
- ✅ Test files and test data
- ✅ Configuration templates (`.env.example`)
- ✅ Example provider mappings (`.example.json`)

### What's NEVER Safe to Share
- ❌ `.env` files with real API keys
- ❌ Actual invoice PDFs
- ❌ Processing logs with real data
- ❌ Provider mappings learned from your invoices
- ❌ Any files containing personal or business data

### Repository Cleanup Checklist
```bash
# Before making public, ensure these are clean:
rm -f .env
rm -f invoice_processor.log
rm -rf input_invoices/
rm -rf processed_invoices/
rm -f provider_mappings.json
rm -f provider_mappings.json.bak
rm -rf __pycache__/
rm -f .DS_Store
```

## 🛠️ Development Security

### For Contributors
1. **Never request real API keys** in issues or PRs
2. **Use mock data** for testing and examples
3. **Sanitize all logs** and error messages
4. **Follow data minimization principles**

### Code Review Checklist
- [ ] No hardcoded credentials
- [ ] Proper error handling without data leakage
- [ ] Secure file operations with proper permissions
- [ ] Input validation and sanitization
- [ ] Appropriate logging levels

## 🚨 Incident Response

If you discover a security issue:
1. **Do not open a public issue**
2. **Email security details** to the project maintainers
3. **Include steps to reproduce** (with safe test data)
4. **Wait for disclosure** coordination

## 📊 Data Flow and Privacy

```
Input PDFs → Text Extraction → OpenAI API → Provider Mapping → Output Files
     ↓              ↓              ↓              ↓              ↓
   Local        Local         Encrypted      Local         Local
 Storage      Memory        HTTPS Call     Storage       Storage
```

### Data Retention
- **Input files**: User-controlled retention
- **Processing logs**: Configurable retention (default: indefinite)
- **API calls**: Not stored by OpenAI after processing
- **Provider mappings**: User-controlled storage

## 🔐 API Key Security

### OpenAI API Key Best Practices
1. **Use organization-level keys** when possible
2. **Set usage limits** and billing alerts
3. **Rotate keys every 90 days**
4. **Monitor usage** for unusual activity
5. **Revoke immediately** if compromised

### Key Permissions
```json
{
  "permissions": [
    "chat.completions.create"
  ],
  "restrictions": {
    "ip_whitelist": ["your_server_ip"],
    "usage_limits": {
      "requests_per_minute": 60,
      "tokens_per_month": 1000000
    }
  }
}
```

## 🌍 Compliance Considerations

### GDPR/Privacy Laws
- **Data processing**: User is responsible for compliance
- **Data retention**: User controls retention policies
- **Data subject rights**: User must handle requests
- **Cross-border transfers**: OpenAI processes data internationally

### Financial Data Regulations
- **PCI DSS**: Not applicable (no payment card data)
- **SOX**: User responsibility for financial data
- **Industry specific**: User must ensure compliance

## 📞 Security Contact

For security concerns or vulnerabilities:
- **Email**: security@yourproject.com
- **PGP Key**: [Available on request]
- **Response time**: Within 48 hours

---

**Remember**: You are responsible for securing your own data and API keys. This project provides tools, but security is your responsibility.

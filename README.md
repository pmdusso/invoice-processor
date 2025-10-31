# Advanced Invoice Processing System

A sophisticated AI-powered invoice processing system that extracts information from PDF invoices using OpenAI's GPT models, provides intelligent provider recognition, and offers comprehensive analytics and export capabilities.

## 🌟 Key Features

### Core Processing
- **AI-Powered Extraction**: Uses OpenAI GPT models (GPT-4, GPT-5) for accurate data extraction
- **Smart Provider Recognition**: Local pattern matching reduces API calls and costs
- **Automatic Learning**: System learns new provider patterns and updates mappings
- **Currency Conversion**: USD to BRL conversion with live or fixed rates
- **Conflict Resolution**: Handles duplicate filenames automatically with timestamps

### Advanced Capabilities
- **Multiple Processing Modes**: Process, Validate, and Dry-run modes
- **Comprehensive Analytics**: Detailed statistics, performance metrics, and error analysis
- **Export Options**: CSV and JSON export for audit trails and analysis
- **Enterprise Testing**: Comprehensive test suite with edge case coverage
- **Progress Tracking**: Real-time progress bars and detailed logging

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <repository_url>
cd process_invoices

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file with your settings:
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
OPENAI_MODEL=gpt-5-2025-08-07
USE_LIVE_EXCHANGE_RATES=false
FALLBACK_EXCHANGE_RATE=5.74
```

### 3. Basic Usage
```bash
# Place PDFs in input_invoices/ folder
mkdir input_invoices
# Add your PDF files...

# Process invoices
python improved_invoice_processor.py

# Check processed_invoices/ for results
```

## 📋 Processing Modes

### Normal Processing (Default)
```bash
python improved_invoice_processor.py
```
- Extracts data and saves processed files
- Updates provider mappings automatically
- Full logging and error handling

### Validation Mode (Fast)
```bash
python improved_invoice_processor.py --mode validate --stats
```
- Validates PDF integrity without API calls
- Ultra-fast file checking (milliseconds per file)
- Identifies corrupted or unreadable files

### Dry Run Mode (Safe Testing)
```bash
python improved_invoice_processor.py --mode dry-run --stats
```
- Extracts data but doesn't save files
- Perfect for testing and cost estimation
- Shows what would be processed

## 📊 Analytics and Export

### Generate Statistics
```bash
python improved_invoice_processor.py --stats
```

### Export Results
```bash
# CSV Export (for spreadsheets)
python improved_invoice_processor.py --export-csv results.csv --stats

# JSON Export (detailed analysis)
python improved_invoice_processor.py --export-json results.json --stats

# Both formats
python improved_invoice_processor.py --export-csv results.csv --export-json results.json --stats
```

### Example Statistics Output
```
--- Processing Statistics ---
Total Files: 21
Successful: 21
Failed: 0
Success Rate: 100.0%

--- Provider Breakdown ---
Cognition AI Inc.: 15 files
Cursor: 3 files
OpenAI, LLC: 1 files
Anthropic, PBC: 1 files
MARSX INC: 1 files

--- Amount Statistics ---
Total USD: $1,712.89
Total BRL: R$9,832.06
Average USD: $81.57
Range USD: $1.20 - $1,047.23

--- Performance Statistics ---
Total Processing Time: 179.3 seconds
Average Time per File: 8.5 seconds
```

## ⚙️ Configuration Options

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-2025-08-07

# Exchange Rate Settings
USE_LIVE_EXCHANGE_RATES=false
FALLBACK_EXCHANGE_RATE=5.74
```

### Command Line Arguments
```bash
python improved_invoice_processor.py [OPTIONS]

Options:
  --input, -i PATH          Input folder (default: input_invoices)
  --output, -o PATH         Output folder (default: processed_invoices)
  --mode MODE               Processing mode: process, validate, dry-run
  --live-rates              Use live exchange rates
  --export-csv PATH         Export results to CSV
  --export-json PATH        Export results to JSON
  --stats                   Show processing statistics
  --debug                   Enable debug logging
```

## 🧪 Testing

### Run Test Suite
```bash
# Run all tests
python test_invoice_processor.py

# Run provider mapping tests
python test_provider_mapping.py
```

### Test Coverage
- ✅ Core functionality tests
- ✅ Error handling and edge cases
- ✅ Provider mapping system
- ✅ File validation and corruption handling
- ✅ API failure scenarios
- ✅ Permission and security issues

## 📁 File Structure

```
process_invoices/
├── improved_invoice_processor.py    # Main processor with advanced features
├── process_invoices.py              # Basic processor (legacy)
├── provider_mapping.py              # Provider recognition system
├── provider_mappings.json           # Provider pattern database
├── test_invoice_processor.py        # Comprehensive test suite
├── test_provider_mapping.py         # Provider mapping tests
├── requirements.txt                 # Python dependencies
├── .env                             # Environment configuration
├── .gitignore                      # Git ignore rules
├── input_invoices/                 # Source PDF files
├── processed_invoices/             # Processed results
├── examples_advanced_usage.md      # Advanced usage examples
└── invoice_processor.log           # Processing logs
```

## 🔧 Provider Mapping System

The `provider_mappings.json` file contains regex patterns for automatic provider recognition:

### Automatic Learning
When OpenAI identifies a new provider, the system automatically:
1. Creates a regex pattern from the provider name
2. Adds it to the mapping file with confidence score
3. Uses the pattern for future processing (reducing API calls)

### Manual Configuration
```json
{
  "mappings": [
    {
      "pattern": "cursor\\.ai",
      "provider": "Cursor",
      "confidence": 1.0,
      "source": "manual"
    }
  ]
}
```

### Backup and Recovery
- Automatic backups created before any changes
- Restore with: `python -c "from provider_mapping import ProviderMapper; ProviderMapper().restore_from_backup()"`

## 📈 Performance Optimization

### Best Practices
1. **Use validation mode first** to check file integrity
2. **Dry run mode** helps estimate processing costs
3. **Provider mappings** significantly reduce API calls
4. **Batch processing** is more efficient than individual files

### Performance Metrics
- **Validation**: ~100 files/second
- **Processing**: ~8-12 seconds per file (with API calls)
- **Memory usage**: ~50MB for large batches
- **API cost reduction**: 60-80% with provider mappings

## 🔍 Troubleshooting

### Common Issues

**API Key Problems**
```bash
# Check if API key is loaded correctly
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(bool(os.getenv('OPENAI_API_KEY')))"
```

**File Permission Errors**
```bash
# Check folder permissions
ls -la input_invoices/ processed_invoices/
```

**PDF Processing Errors**
- Ensure PDFs are text-based (not scanned images)
- Check if PDFs are encrypted
- Use validation mode to test file readability

**Provider Mapping Issues**
```bash
# Validate mapping file syntax
python -c "import json; print(json.load(open('provider_mappings.json')))"
```

### Debug Mode
```bash
# Enable detailed logging
python improved_invoice_processor.py --debug
```

## 🚀 Advanced Use Cases

### Batch Analysis
```bash
# Analyze large batch without processing
python improved_invoice_processor.py --mode dry-run --export-json batch_analysis.json --stats
```

### Quality Assurance
```bash
# Validate all files before processing
python improved_invoice_processor.py --mode validate --export-csv qa_report.csv --stats
```

### Audit Trail
```bash
# Complete processing with audit trail
python improved_invoice_processor.py --export-json audit_$(date +%Y%m%d).json --export-csv summary_$(date +%Y%m%d).csv --stats
```

### Scheduled Processing (Cron)
```bash
# Daily processing at 2 AM
0 2 * * * cd /path/to/invoice_processor && python improved_invoice_processor.py --export-json /logs/$(date +\%Y\%m\%d)_results.json --stats >> /logs/$(date +\%Y\%m\%d)_processing.log 2>&1
```

## 📚 Documentation

- **[Advanced Usage Examples](examples_advanced_usage.md)** - Detailed usage scenarios
- **[Task Plan](task_plan/improvement_plan.md)** - Development roadmap and completed features
- **[Provider Mapping Tasks](task_plan/provider_mapping_tasks.md)** - Provider system implementation details

## 🛠️ Development

### Code Quality
- **Type hints** throughout the codebase
- **Comprehensive logging** with configurable levels
- **Error handling** with specific exception types
- **Atomic file operations** to prevent corruption
- **Input validation** and sanitization

### Architecture
- **Modular design** with separate components
- **Provider mapping** system for cost optimization
- **Flexible configuration** via environment and CLI
- **Export system** with multiple format support
- **Testing framework** with high coverage

## 📄 Requirements

```txt
PyPDF2==3.0.1
openai>=1.76.2
forex-python==1.8
python-dotenv==1.0.0
tqdm==4.66.1
```

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the log files (`invoice_processor.log`)
3. Run validation mode to diagnose file issues
4. Enable debug mode for detailed diagnostics

---

**Enterprise-grade invoice processing with AI-powered accuracy and comprehensive analytics.** 
# Advanced Invoice Processor Usage Examples

This document demonstrates the advanced features of the improved invoice processor.

## Processing Modes

### 1. Normal Processing (Default)
```bash
# Standard processing - extracts data and saves files
python improved_invoice_processor.py

# With custom folders
python improved_invoice_processor.py --input /path/to/invoices --output /path/to/processed
```

### 2. Validation Mode
```bash
# Validate PDF files without processing - fast check for file integrity
python improved_invoice_processor.py --mode validate --stats

# Export validation results to CSV
python improved_invoice_processor.py --mode validate --export-csv validation_report.csv
```

### 3. Dry Run Mode
```bash
# Extract data but don't save files - perfect for testing
python improved_invoice_processor.py --mode dry-run --stats

# Export dry run results to JSON
python improved_invoice_processor.py --mode dry-run --export-json dry_run_results.json
```

## Export Options

### CSV Export
```bash
# Export processing results to CSV format
python improved_invoice_processor.py --export-csv results.csv --stats
```

### JSON Export
```bash
# Export detailed results to JSON format
python improved_invoice_processor.py --export-json results.json --stats
```

### Both Formats
```bash
# Export to both CSV and JSON
python improved_invoice_processor.py --export-csv results.csv --export-json results.json --stats
```

## Statistics and Analytics

### Basic Statistics
```bash
# Show processing statistics
python improved_invoice_processor.py --stats
```

### Combined Features
```bash
# Dry run with statistics and export
python improved_invoice_processor.py --mode dry-run --stats --export-csv analysis.csv --export-json analysis.json
```

## Example Output

### Statistics Summary
```
--- Processing Statistics ---
Total Files: 21
Successful: 21
Failed: 0
Success Rate: 100.0%

--- Provider Breakdown ---
Cognition AI Inc.: 15 files
Cursor: 3 files
MARSX INC: 1 files
OpenAI, LLC: 1 files
Anthropic, PBC: 1 files

--- Amount Statistics ---
Total USD: $1712.89
Total BRL: R$9832.06
Average USD: $81.57
Average BRL: R$468.19
Range USD: $1.20 - $1047.23

--- Performance Statistics ---
Total Processing Time: 179.3 seconds
Average Time per File: 8.5 seconds
Fastest File: 4.6 seconds
Slowest File: 18.1 seconds
```

### CSV Export Format
```csv
filename,provider,date,usd_amount,brl_amount,status,error_message,processing_time,output_filename
Invoice-GANJIUUM-0001.pdf,Cognition AI Inc.,10_10_2025,20.0,114.8,success,,4.93,Cognition AI Inc. - 10_10_2025 - USD 20.0 - BRL 114.8.pdf
```

### JSON Export Format
```json
{
  "export_timestamp": "2025-10-31T11:31:04.956481",
  "total_files": 21,
  "successful": 21,
  "failed": 0,
  "results": [
    {
      "filename": "Invoice-GANJIUUM-0001.pdf",
      "status": "success",
      "provider": "Cognition AI Inc.",
      "date": "10_10_2025",
      "usd_amount": 20.0,
      "brl_amount": 114.8,
      "processing_time": 4.931234
    }
  ]
}
```

## Use Cases

### 1. Batch Analysis
```bash
# Analyze a large batch of invoices without processing
python improved_invoice_processor.py --mode dry-run --stats --export-json batch_analysis.json
```

### 2. Quality Assurance
```bash
# Validate all PDFs before processing
python improved_invoice_processor.py --mode validate --export-csv qa_report.csv --stats
```

### 3. Cost Estimation
```bash
# Dry run to estimate API costs before actual processing
python improved_invoice_processor.py --mode dry-run --stats
```

### 4. Audit Trail
```bash
# Process with full logging and export
python improved_invoice_processor.py --export-json audit_trail.json --export-csv audit_summary.csv --stats
```

## Performance Tips

1. **Use validation mode first** to check file integrity
2. **Dry run mode** helps estimate processing time and costs
3. **Export to JSON** for detailed analysis and backup
4. **Export to CSV** for spreadsheet analysis
5. **Statistics mode** provides insights into processing patterns

## Integration Examples

### Python Script Integration
```python
import subprocess
import json

# Run dry run and capture results
result = subprocess.run([
    "python", "improved_invoice_processor.py",
    "--mode", "dry-run",
    "--export-json", "temp_results.json"
], capture_output=True, text=True)

# Load and analyze results
with open("temp_results.json") as f:
    data = json.load(f)
    
print(f"Processed {data['total_files']} files")
print(f"Success rate: {data['successful']/data['total_files']*100:.1f}%")
```

### Cron Job for Scheduled Processing
```bash
# Add to crontab for daily processing at 2 AM
0 2 * * * cd /path/to/invoice_processor && python improved_invoice_processor.py --export-json /logs/$(date +\%Y\%m\%d)_results.json --stats >> /logs/$(date +\%Y\%m\%d)_processing.log 2>&1
```

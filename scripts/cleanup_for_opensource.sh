#!/bin/bash

# Cleanup script to prepare repository for open source release
# This removes all sensitive data and prepares a clean repository

echo "🧹 Cleaning repository for open source release..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "improved_invoice_processor.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Backup current state (optional)
read -p "Do you want to create a backup before cleaning? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    print_status "Creating backup in $BACKUP_DIR..."
    mkdir -p "../$BACKUP_DIR"
    cp -r . "../$BACKUP_DIR/"
    print_status "Backup created at ../$BACKUP_DIR"
fi

# Remove sensitive files
print_status "Removing sensitive files..."

# Files that should never be in open source
if [ -f ".env" ]; then
    print_warning "Removing .env file (contains API keys)"
    rm -f .env
fi

if [ -f "invoice_processor.log" ]; then
    print_warning "Removing invoice_processor.log (contains sensitive data)"
    rm -f invoice_processor.log
fi

# Remove actual invoice data
if [ -d "input_invoices" ]; then
    print_warning "Removing input_invoices/ directory (contains actual invoices)"
    rm -rf input_invoices
fi

if [ -d "processed_invoices" ]; then
    print_warning "Removing processed_invoices/ directory (contains processed invoices)"
    rm -rf processed_invoices
fi

# Remove learned provider mappings (contain patterns from your data)
if [ -f "provider_mappings.json" ]; then
    print_warning "Removing provider_mappings.json (contains learned patterns from your data)"
    rm -f provider_mappings.json
fi

if [ -f "provider_mappings.json.bak" ]; then
    print_warning "Removing provider_mappings.json.bak (backup of your learned patterns)"
    rm -f provider_mappings.json.bak
fi

# Remove temporary files
print_status "Removing temporary files..."
rm -rf __pycache__/
rm -rf .pytest_cache/
rm -rf .coverage
rm -f .DS_Store
rm -f *.pyc
rm -f *.pyo
rm -f *.pyd
rm -f *.log

# Create placeholder directories with .gitkeep
print_status "Creating placeholder directories..."
mkdir -p input_invoices
touch input_invoices/.gitkeep
echo "# This directory is for input invoice PDFs" > input_invoices/README.md
echo "# Place your PDF invoices here for processing" >> input_invoices/README.md

mkdir -p processed_invoices
touch processed_invoices/.gitkeep
echo "# This directory is for processed invoice files" > processed_invoices/README.md
echo "# Processed invoices will appear here after running the processor" >> processed_invoices/README.md

# Verify .gitignore is comprehensive
print_status "Checking .gitignore..."
if ! grep -q ".env" .gitignore; then
    echo ".env" >> .gitignore
fi

if ! grep -q "*.log" .gitignore; then
    echo "*.log" >> .gitignore
fi

if ! grep -q "invoice_processor.log" .gitignore; then
    echo "invoice_processor.log" >> .gitignore
fi

# Create example files if they don't exist
if [ ! -f ".env.example" ]; then
    print_status "Creating .env.example..."
    cp .env.example .env.example 2>/dev/null || echo "# OpenAI API key
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
USE_LIVE_EXCHANGE_RATES=false
FALLBACK_EXCHANGE_RATE=5.74" > .env.example
fi

if [ ! -f "provider_mappings.example.json" ]; then
    print_status "Creating provider_mappings.example.json..."
    cp provider_mappings.example.json provider_mappings.example.json 2>/dev/null || echo '{"version": "1.0.0", "mappings": []}' > provider_mappings.example.json
fi

# Check for any remaining sensitive data
print_status "Scanning for remaining sensitive data..."

# Check for potential API keys in Python files
if grep -r "sk-" --include="*.py" .; then
    print_error "Found potential API keys in Python files!"
    print_error "Please remove any hardcoded API keys before proceeding."
fi

# Check for potential email addresses or personal data
if grep -r -E "\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b" --include="*.py" --include="*.md" .; then
    print_warning "Found potential email addresses. Please review and remove if personal."
fi

# Final status
print_status "Cleanup completed!"
echo
echo "📋 Summary of actions taken:"
echo "  ✅ Removed .env file"
echo "  ✅ Removed log files"
echo "  ✅ Removed actual invoice data"
echo "  ✅ Removed learned provider mappings"
echo "  ✅ Removed temporary files"
echo "  ✅ Created placeholder directories"
echo "  ✅ Created example configuration files"
echo
echo "🔍 Please review the following before committing:"
echo "  - Check for any remaining sensitive data"
echo "  - Test that the setup instructions work"
echo "  - Verify all example files are generic"
echo "  - Ensure documentation doesn't contain personal information"
echo
echo "🚀 Your repository is now ready for open source release!"
echo
echo "Next steps:"
echo "  1. Review the changes: git status"
echo "  2. Add the changes: git add ."
echo "  3. Commit: git commit -m 'Prepare for open source release'"
echo "  4. Push to GitHub and publish!"

#!/bin/bash

# Backup your local sensitive data before open source operations
# and restore it when needed

BACKUP_DIR="$HOME/.invoice_processor_backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

case "$1" in
    "backup")
        print_status "Backing up local sensitive data..."
        
        # Backup provider mappings
        if [ -f "provider_mappings.json" ]; then
            cp provider_mappings.json "$BACKUP_DIR/provider_mappings_$TIMESTAMP.json"
            print_status "✅ Backed up provider_mappings.json"
        fi
        
        # Backup environment file
        if [ -f ".env" ]; then
            cp .env "$BACKUP_DIR/env_$TIMESTAMP"
            print_status "✅ Backed up .env"
        fi
        
        # Backup logs if they exist
        if [ -f "invoice_processor.log" ]; then
            cp invoice_processor.log "$BACKUP_DIR/invoice_processor_$TIMESTAMP.log"
            print_status "✅ Backed up invoice_processor.log"
        fi
        
        print_status "Backup completed in $BACKUP_DIR"
        ;;
        
    "restore")
        print_status "Restoring local sensitive data..."
        
        # Find latest backup files
        LATEST_MAPPINGS=$(ls -t "$BACKUP_DIR"/provider_mappings_*.json 2>/dev/null | head -1)
        LATEST_ENV=$(ls -t "$BACKUP_DIR"/env_* 2>/dev/null | head -1)
        LATEST_LOG=$(ls -t "$BACKUP_DIR"/invoice_processor_*.log 2>/dev/null | head -1)
        
        # Restore provider mappings
        if [ -n "$LATEST_MAPPINGS" ]; then
            cp "$LATEST_MAPPINGS" provider_mappings.json
            print_status "✅ Restored provider_mappings.json"
        else
            print_warning "No provider mappings backup found"
        fi
        
        # Restore environment file
        if [ -n "$LATEST_ENV" ]; then
            cp "$LATEST_ENV" .env
            print_status "✅ Restored .env"
        else
            print_warning "No .env backup found"
        fi
        
        # Restore log file
        if [ -n "$LATEST_LOG" ]; then
            cp "$LATEST_LOG" invoice_processor.log
            print_status "✅ Restored invoice_processor.log"
        else
            print_warning "No log backup found"
        fi
        
        print_status "Restore completed"
        ;;
        
    "list")
        print_status "Available backups:"
        echo
        echo "Provider Mappings:"
        ls -la "$BACKUP_DIR"/provider_mappings_*.json 2>/dev/null || echo "  None found"
        echo
        echo "Environment Files:"
        ls -la "$BACKUP_DIR"/env_* 2>/dev/null || echo "  None found"
        echo
        echo "Log Files:"
        ls -la "$BACKUP_DIR"/invoice_processor_*.log 2>/dev/null || echo "  None found"
        ;;
        
    "clean")
        print_warning "This will delete all backups. Are you sure? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "$BACKUP_DIR"
            print_status "All backups deleted"
        else
            print_status "Cancelled"
        fi
        ;;
        
    *)
        echo "Usage: $0 {backup|restore|list|clean}"
        echo
        echo "Commands:"
        echo "  backup  - Backup your local sensitive data"
        echo "  restore - Restore your local sensitive data"
        echo "  list    - List available backups"
        echo "  clean   - Delete all backups"
        exit 1
        ;;
esac

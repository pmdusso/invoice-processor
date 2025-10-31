# 📁 Local Data Management Guide

This guide shows you how to keep your personal data while maintaining an open source repository.

## 🎯 **Your Current Situation**

✅ **Perfect Setup**: Your `provider_mappings.json` is already properly configured:
- **File exists locally** with all your learned patterns
- **Not tracked by git** (removed from tracking)
- **Protected by .gitignore** (won't be accidentally committed)
- **Usable by your scripts** (works normally)

## 🔄 **Recommended Workflow**

### **Option 1: Keep as Local File (Simplest)**
```bash
# Your current setup is already perfect!
# The file stays on your computer but won't be committed

# Verify it's working:
python improved_invoice_processor.py --help  # Should work fine

# Verify it's ignored:
git status  # Should not show provider_mappings.json
```

### **Option 2: Backup Before Open Source**
```bash
# Create a backup of your data
./scripts/backup_local_data.sh backup

# This creates backups in ~/.invoice_processor_backup/
# - provider_mappings_YYYYMMDD_HHMMSS.json
# - env_YYYYMMDD_HHMMSS
# - invoice_processor_YYYYMMDD_HHMMSS.log
```

### **Option 3: Personal Branch**
```bash
# Create a branch for your personal data
git checkout -b personal-data
git add provider_mappings.json .env
git commit -m "Add personal configuration and mappings"

# Switch back to main for open source work
git checkout main

# Switch to personal data when needed:
git checkout personal-data
```

## 🛠️ **Practical Commands**

### **Daily Use (Recommended)**
```bash
# Work on main branch (open source ready)
git checkout main

# Your local files still work:
python improved_invoice_processor.py

# Git operations are safe:
git add .
git commit -m "Update documentation"  # Won't include sensitive files
git push  # Pushes only clean code
```

### **When You Need to Update Mappings**
```bash
# Process invoices normally
python improved_invoice_processor.py

# Your provider_mappings.json gets updated automatically
# But it still won't be committed because it's ignored

# If you want to save the updated mappings to your personal branch:
git checkout personal-data
cp provider_mappings.json ../temp_mappings.json
git checkout main
cp ../temp_mappings.json provider_mappings.json
rm ../temp_mappings.json
```

### **Before Major Git Operations**
```bash
# Backup your data first
./scripts/backup_local_data.sh backup

# Now you can safely:
git rebase
git merge
git reset --hard
# etc.

# Restore if needed:
./scripts/backup_local_data.sh restore
```

## 📋 **Verification Commands**

### **Check Your Setup**
```bash
# Verify sensitive files are ignored:
python scripts/verify_gitignore.py

# Check what git sees:
git status
git ls-files  # Should not show provider_mappings.json

# Check what files exist locally:
ls -la provider_mappings.json .env
```

### **Test Functionality**
```bash
# Test that your local setup still works:
python improved_invoice_processor.py --mode validate

# Should use your local provider mappings
```

## 🔧 **Advanced Options**

### **Using Git Skip-Worktree**
```bash
# If you ever add the file back to git and want to ignore changes:
git add provider_mappings.json
git update-index --skip-worktree provider_mappings.json

# To undo this later:
git update-index --no-skip-worktree provider_mappings.json
```

### **Using Git Assume-Uncanged**
```bash
# Alternative approach:
git add provider_mappings.json
git update-index --assume-unchanged provider_mappings.json

# To undo:
git update-index --no-assume-unchanged provider_mappings.json
```

## 🚨 **Important Reminders**

### **NEVER Do These**
```bash
# ❌ Don't add your sensitive files to git:
git add provider_mappings.json

# ❌ Don't commit sensitive data:
git commit -m "Update mappings"  # If provider_mappings.json is staged

# ❌ Don't force add ignored files:
git add -f provider_mappings.json
```

### **ALWAYS Do These**
```bash
# ✅ Always verify before committing:
git status
python scripts/verify_gitignore.py

# ✅ Always backup before major operations:
./scripts/backup_local_data.sh backup

# ✅ Always check what you're pushing:
git diff --cached origin/main
```

## 📁 **File Locations**

### **Your Local Data**
```
/Users/pmdusso/code/process_invoices/
├── provider_mappings.json          # ✅ Your personal mappings (ignored)
├── .env                           # ✅ Your API keys (ignored)
├── invoice_processor.log          # ✅ Your logs (ignored)
└── input_invoices/                # ✅ Your invoices (ignored)
```

### **Backup Location**
```
~/.invoice_processor_backup/
├── provider_mappings_20251031_143022.json
├── env_20251031_143022
└── invoice_processor_20251031_143022.log
```

## 🎉 **Summary**

Your current setup is **perfect** for open source:

1. **Keep using your local files normally**
2. **They won't be committed to git**
3. **Your open source repository stays clean**
4. **You can backup/restore when needed**

**No additional action required!** Your provider_mappings.json is safe and will continue to work locally while keeping your open source repository clean.

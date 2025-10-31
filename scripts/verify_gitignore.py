#!/usr/bin/env python3
"""
Verify that all sensitive files are properly ignored by .gitignore
This script checks for files that should be ignored but might accidentally be tracked.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Tuple

def run_git_command(cmd: List[str]) -> Tuple[bool, str]:
    """Run a git command and return success status and output."""
    try:
        result = subprocess.run(
            ['git'] + cmd, 
            capture_output=True, 
            text=True, 
            check=True
        )
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        return False, e.stderr.strip()
    except FileNotFoundError:
        return False, "Git not found"

def check_git_repository() -> bool:
    """Check if we're in a git repository."""
    success, _ = run_git_command(['rev-parse', '--git-dir'])
    return success

def get_tracked_files() -> List[str]:
    """Get list of files currently tracked by git."""
    success, output = run_git_command(['ls-files'])
    if not success:
        return []
    return output.split('\n') if output else []

def get_ignored_files() -> List[str]:
    """Get list of files ignored by .gitignore."""
    success, output = run_git_command(['status', '--ignored', '--porcelain'])
    if not success:
        return []
    
    ignored_files = []
    for line in output.split('\n'):
        if line.startswith('!! '):
            ignored_files.append(line[3:])
    return ignored_files

def check_sensitive_files() -> List[Tuple[str, str]]:
    """Check for sensitive files that should not be tracked."""
    sensitive_patterns = {
        '.env': 'Environment file with API keys',
        'provider_mappings.json': 'Provider mappings with learned patterns',
        'provider_mappings.json.bak': 'Backup of provider mappings',
        'invoice_processor.log': 'Processing logs with sensitive data',
        'input_invoices/': 'Directory with actual invoice PDFs',
        'processed_invoices/': 'Directory with processed invoices',
        '*.log': 'Log files',
        '*.csv': 'Export files with real data',
        '*.json': 'JSON files (except examples)',
        'processing_results.': 'Processing results with real data',
        'validation_results.': 'Validation results with real data',
        'audit_': 'Audit files with sensitive data',
        'batch_': 'Batch processing results',
        'analysis_': 'Analysis files with real data',
    }
    
    issues = []
    tracked_files = get_tracked_files()
    
    for pattern, description in sensitive_patterns.items():
        # Check if any tracked files match the pattern
        for tracked_file in tracked_files:
            if pattern.startswith('*.'):
                # Wildcard pattern
                if tracked_file.endswith(pattern[1:]):
                    issues.append((tracked_file, description))
            elif pattern.endswith('/'):
                # Directory pattern
                if tracked_file.startswith(pattern):
                    issues.append((tracked_file, description))
            elif pattern.endswith('.'):
                # Extension pattern
                if tracked_file.startswith(pattern.replace('.', '')):
                    issues.append((tracked_file, description))
            elif pattern in tracked_file:
                # Contains pattern
                issues.append((tracked_file, description))
    
    return issues

def check_example_files_exist() -> List[Tuple[str, str]]:
    """Check that example files exist for sensitive files."""
    required_examples = {
        '.env.example': 'Example environment file',
        'provider_mappings.example.json': 'Example provider mappings',
    }
    
    missing_examples = []
    for example_file, description in required_examples.items():
        if not Path(example_file).exists():
            missing_examples.append((example_file, description))
    
    return missing_examples

def check_gitignore_completeness() -> List[str]:
    """Check if .gitignore contains all necessary patterns."""
    required_patterns = [
        '.env',
        'provider_mappings.json',
        '*.log',
        'input_invoices/',
        'processed_invoices/',
        '*.csv',
        '*.json',
        'processing_results.*',
        'validation_results.*',
    ]
    
    gitignore_path = Path('.gitignore')
    if not gitignore_path.exists():
        return ['.gitignore file not found']
    
    with open(gitignore_path, 'r') as f:
        gitignore_content = f.read()
    
    missing_patterns = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing_patterns.append(pattern)
    
    return missing_patterns

def main():
    """Main verification function."""
    print("🔍 Verifying .gitignore configuration for open source readiness...")
    print("=" * 70)
    
    # Check if we're in a git repository
    if not check_git_repository():
        print("❌ Not in a git repository")
        return 1
    
    issues_found = False
    
    # Check for tracked sensitive files
    print("🚨 Checking for tracked sensitive files...")
    sensitive_issues = check_sensitive_files()
    if sensitive_issues:
        issues_found = True
        print("❌ Sensitive files found in git:")
        for file_path, description in sensitive_issues:
            print(f"   - {file_path} ({description})")
        print("\n💡 To remove these files from git:")
        for file_path, _ in sensitive_issues:
            print(f"   git rm --cached {file_path}")
    else:
        print("✅ No sensitive files tracked")
    
    print()
    
    # Check example files
    print("📝 Checking for example files...")
    missing_examples = check_example_files_exist()
    if missing_examples:
        issues_found = True
        print("❌ Missing example files:")
        for example_file, description in missing_examples:
            print(f"   - {example_file} ({description})")
    else:
        print("✅ All required example files exist")
    
    print()
    
    # Check .gitignore completeness
    print("📋 Checking .gitignore completeness...")
    missing_patterns = check_gitignore_completeness()
    if missing_patterns:
        issues_found = True
        print("❌ Missing patterns in .gitignore:")
        for pattern in missing_patterns:
            print(f"   - {pattern}")
    else:
        print("✅ .gitignore contains all required patterns")
    
    print()
    
    # Check ignored files
    print("🔒 Checking currently ignored files...")
    ignored_files = get_ignored_files()
    important_ignored = [f for f in ignored_files if any(pattern in f for pattern in [
        '.env', 'provider_mappings', '.log', 'input_invoices', 'processed_invoices'
    ])]
    
    if important_ignored:
        print("✅ Important files properly ignored:")
        for ignored_file in important_ignored[:10]:  # Show first 10
            print(f"   - {ignored_file}")
        if len(important_ignored) > 10:
            print(f"   ... and {len(important_ignored) - 10} more")
    else:
        print("⚠️  No important files currently ignored (might be clean state)")
    
    print()
    print("=" * 70)
    
    if issues_found:
        print("❌ Issues found! Please address them before making the repository public.")
        print("\n📖 See OPEN_SOURCE_PREPARATION.md for guidance.")
        return 1
    else:
        print("✅ All checks passed! Repository is ready for open source.")
        print("\n🚀 You can safely make this repository public.")
        return 0

if __name__ == "__main__":
    exit(main())

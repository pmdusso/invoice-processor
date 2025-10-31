# Invoice Processor Improvement Plan

## Security Issues
- [x] **Remove hardcoded API key** - Store OpenAI API key in environment variables or a secure configuration file

## Code Quality Improvements
- [x] **Fix unused imports** - Remove or use the imported `CurrencyRates` from forex_python
- [x] **Standardize path handling** - Use pathlib.Path consistently throughout the code
- [x] **Fix process_file() return values** - Ensure consistent return of True/False for proper failed file tracking
- [x] **Eliminate duplicate filename sanitization** - Consolidate the two separate sanitization methods
- [x] **Add file existence checks** - Prevent accidental overwrites of existing files during renaming
- [x] **Add type hints** - Implement comprehensive type annotations for all functions
- [x] **Implement proper logging** - Replace print statements with the logging module
- [x] **Add input validation** - Validate input data before processing (added currency, date, amount validation)
- [x] **Add error handling** - Improve exception handling with specific exception types
- [x] **Make configuration flexible** - Allow configuring API key, folders, models, etc. through environment variables
- [x] **Remove hardcoded paths** - Use relative paths for input/output folders

## New Features
- [x] **Add progress tracking** - Show progress during processing of multiple files
- [x] **Add configurable exchange rates** - Allow configuration of live or fixed exchange rates
- [x] **Add CLI arguments** - Support command-line arguments for easier configuration
- [x] **Add file conflict resolution** - Handle filename conflicts automatically (append counter)
- [x] **Enable copying instead of renaming** - Copy processed files to output folder instead of renaming in place

## Infrastructure Improvements
- [x] **Create requirements.txt** - Document all dependencies
- [x] **Create README.md** - Add usage instructions and examples
- [x] **Create example .env file** - Provide template for environment variables

## File Handling Improvements
- [x] **Read input files from input folder and output them to an output folder** - Implement structured file organization

## Functional Enhancements
- [x] **Separate input/output folders** - Modify code to read from input folder and write to output folder
- [x] **Dynamic currency conversion** - Use the forex_python library for real-time conversion rates
- [x] **Configurable parameters** - Make model name, folder paths, and other settings configurable
- [x] **Progress tracking** - Add better progress indicators for batch processing (used tqdm)

## Documentation
- [x] **Add comprehensive docstrings** - Document all functions with proper docstrings following PEP 257
- [x] **Create usage examples** - Add examples showing how to use the script (in README)
- [x] **Document configuration options** - Clear documentation for all configurable parameters (in README/env.example)

## Deployment Considerations
- [x] **Add setup instructions** - Clear setup guide including environment variables (in README) 
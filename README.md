# Invoice Processing Script

This script processes PDF invoices located in the `input_invoices` folder, extracts key details using AI (OpenAI GPT-4) and a local provider mapping system, renames the files based on extracted information (Provider - Date - Amount), and saves them to the `processed_invoices` folder.

## Features

*   Extracts text from PDF files.
*   Identifies Service Provider, Date, and Amount (in USD).
*   Uses a local JSON mapping (`provider_mappings.json`) to identify known providers via regex, reducing AI API calls.
*   Learns new provider patterns from AI results and updates the JSON mapping automatically.
*   Converts USD amount to BRL (currently using a fixed rate).
*   Renames processed files to a standard format: `Provider - dd_MM_yyyy - USD Amount - BRL Amount.pdf`.
*   Handles potential filename conflicts by appending numbers.
*   Logs operations and errors to `invoice_processor.log`.
*   Creates automatic backups of the provider mapping file.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd process_invoices
    ```
2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate 
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt 
    ```
4.  **Set up environment variables:**
    Create a `.env` file in the project root directory and add your OpenAI API key:
    ```
    OPENAI_API_KEY=your_openai_api_key_here
    ```

## Usage

1.  Place your PDF invoices into the `input_invoices` folder (create it if it doesn't exist).
2.  Run the script:
    ```bash
    python process_invoices.py
    ```
3.  Processed files will appear in the `processed_invoices` folder.
4.  Check `invoice_processor.log` for detailed logs.

## Provider Mapping (`provider_mappings.json`)

This JSON file helps the script identify providers without calling the OpenAI API every time.

*   **Automatic Learning:** When OpenAI identifies a provider that isn't matched by the current patterns, the script attempts to learn a new pattern and adds it to this file.
*   **Manual Edits:** You can manually add or edit entries in this file. Ensure patterns are valid Python regex.
*   **Backup:** Before any changes are saved, the script automatically creates a backup named `provider_mappings.json.bak`.
*   **Restore:** If `provider_mappings.json` becomes corrupted or you want to revert recent learned changes:
    1.  Delete the corrupted `provider_mappings.json` file.
    2.  Rename `provider_mappings.json.bak` to `provider_mappings.json`.
    Alternatively, you can use the `restore_from_backup()` method in the `ProviderMapper` class programmatically if needed.

## Requirements

(Create a `requirements.txt` file with the following content)

```
python-dotenv
openai
pypdf2
forex-python
```

## Troubleshooting

*   **`ValueError: OpenAI API key not found`**: Ensure you have created a `.env` file in the project root and added your `OPENAI_API_KEY` correctly.
*   **`FileNotFoundError` for input folder**: Make sure the `input_invoices` folder exists in the same directory as the script, or create it.
*   **Errors processing specific PDFs**: Some PDFs might be image-based, encrypted, or have unusual formatting that `PyPDF2` cannot read. Check the PDF manually. The script will log errors for specific files.
*   **Provider mapping file errors (`JSONDecodeError`, `IOError`, `PermissionError`)**: 
    *   Check the logs (`invoice_processor.log`) for specific error messages.
    *   Ensure `provider_mappings.json` is valid JSON if edited manually.
    *   Check file permissions for `provider_mappings.json`.
    *   Try restoring from `provider_mappings.json.bak` if the main file is corrupted (see Restore procedure above).
*   **Invalid regex pattern warnings**: If you manually add patterns to `provider_mappings.json`, ensure they are valid Python regular expressions. The script will log warnings for invalid patterns found during loading or adding.
*   **Incorrect BRL conversion**: The script currently uses a hardcoded BRL rate in `process_invoices.py`. Modify the `convert_usd_to_brl` function if you need live rates or a different fixed rate.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 
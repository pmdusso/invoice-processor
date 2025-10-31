#!/usr/bin/env python3
"""
Invoice Processor - Extracts information from PDF invoices and renames them accordingly.

This script reads PDF invoices from an input folder, extracts key information using
OpenAI's GPT-4 model, converts USD amounts to BRL, and saves the renamed files 
to an output folder with a standardized naming convention.
"""

import os
import sys
import logging
import PyPDF2  # type: ignore # Using type_ignore as stubs aren't available
from typing import Dict, List, Optional, Tuple, Union, cast
from datetime import datetime
from pathlib import Path
from forex_python.converter import CurrencyRates  # type: ignore
from openai import OpenAI
from dotenv import load_dotenv  # type: ignore
from tqdm import tqdm  # type: ignore
import csv
import json as json_module

# Import provider mapping functionality
try:
    from provider_mapping import ProviderMapper
    USE_PROVIDER_MAPPING = True
except ImportError:
    USE_PROVIDER_MAPPING = False
    print("Provider mapping module not found. Will always use OpenAI for provider identification.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("invoice_processor.log")
    ]
)
logger = logging.getLogger("invoice_processor")

# Load environment variables
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Default paths
DEFAULT_INPUT_FOLDER = Path("input_invoices")
DEFAULT_OUTPUT_FOLDER = Path("processed_invoices")

# --- Configuration (Defaults) ---
# These can be overridden by environment variables or command-line args where applicable
OPENAI_MODEL_DEFAULT = "o4-mini"
USE_LIVE_EXCHANGE_RATES_DEFAULT = False
FALLBACK_EXCHANGE_RATE_DEFAULT = 5.74
# --------------------------------

# Initialize provider mapper if available
if USE_PROVIDER_MAPPING:
    provider_mapper = ProviderMapper()
    logger.info(f"Initialized provider mapper with {len(provider_mapper.get_all_mappings())} mappings")

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        str: Extracted text content
        
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        PyPDF2.errors.PdfReadError: If the PDF file is invalid or corrupted
    """
    logger.debug(f"Extracting text from {pdf_path}")
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += page_text
                logger.debug(f"Extracted {len(page_text)} characters from page {page_num+1}")
            
            logger.debug(f"Total extracted: {len(text)} characters")
            return text
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        raise
    except PyPDF2.errors.PdfReadError as e:
        logger.error(f"Error reading PDF {pdf_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting text from {pdf_path}: {str(e)}")
        raise


def get_invoice_details(
    pdf_text: str, client: OpenAI, openai_model: str, logger: logging.Logger,
    use_live_rates: bool = False, fallback_rate: float = 5.74
) -> Tuple[str, str, float, float]:
    """
    Extract invoice details from PDF text using OpenAI API.
    
    Args:
        pdf_text: The text extracted from the PDF
        client: The OpenAI client
        openai_model: The OpenAI model to use
        logger: Logger instance
        use_live_rates: Whether to use live exchange rates
        fallback_rate: Fallback exchange rate when live rates are disabled/unavailable
        
    Returns:
        Tuple containing (provider, date_str, usd_amount, brl_amount)
    """
    # First try identifying the provider using our mapping
    provider_from_mapping = None
    if USE_PROVIDER_MAPPING:
        provider_from_mapping = provider_mapper.identify_provider(pdf_text)
        if provider_from_mapping:
            logger.info(f"Provider identified from mapping: {provider_from_mapping}")
    
    # If we have a provider from mapping, construct the prompt to extract only date and amount
    if provider_from_mapping:
        prompt = (
            f"I already know the service provider is '{provider_from_mapping}'.\n"
            "Extract ONLY the following details from the invoice text and return them in a strict format of 3 elements separated by ' - ':\n"
            "1. Date in dd_MM_yyyy format\n"
            "2. Amount in USD (just the number)\n"
            "3. 'USD'\n\n"
            f"Text from invoice:\n{pdf_text}\n\n"
            "Important: Respond ONLY with the 3 elements separated by ' - ' without any additional text."
        )
    else:
        # Standard prompt to extract all details
        prompt = (
            "Extract the following details from the invoice text and return them in a strict format of 4 elements separated by ' - ':\n"
            "1. Service Provider\n"
            "2. Date in dd_MM_yyyy format\n"
            "3. Amount in USD (just the number)\n"
            "4. 'USD'\n\n"
            f"Text from invoice:\n{pdf_text}\n\n"
            "Important: Respond ONLY with the 4 elements separated by ' - ' without any additional text."
        )
    
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_completion_tokens=10000
            )
            
            # Log the raw response for debugging
            logger.debug(f"Raw OpenAI response: {response}")
            
            # Check if response has content
            if not response.choices or not response.choices[0].message:
                raise ValueError("No choices in OpenAI response")
                
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty content in OpenAI response")
                
            content = content.strip()
            logger.debug(f"Cleaned content: {content}")
            
            if not content:
                raise ValueError("Empty content after stripping")
                
            # If we got here, we have valid content
            break
            
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                logger.error(f"Failed to get valid response from OpenAI after {max_retries} attempts: {str(e)}")
                raise
            
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_delay} seconds...")
            import time
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        
    # Split by delimiter
    details = content.split(" - ")
    logger.debug(f"Split details: {details}")
    
    # Handle parsing based on whether we used provider mapping or not
    try:
        if provider_from_mapping:
            # Parse 3 elements (date, amount, currency)
            if len(details) != 3:
                # Try an alternative approach - maybe the response has newlines instead of spaces
                potential_details = content.replace("\n", " ").split(" - ")
                if len(potential_details) == 3:
                    details = potential_details
                    logger.info("Used alternative parsing approach for OpenAI response")
                else:
                    logger.error(f"Invalid response format from OpenAI (expected 3 elements): {details}")
                    raise ValueError(f"Invalid response format from OpenAI (expected 3 elements): {details}")
            
            date_str, usd_amount_str, currency = details
            provider = provider_from_mapping
        else:
            # Parse 4 elements (provider, date, amount, currency)
            if len(details) != 4:
                # Try an alternative approach - maybe the response has newlines instead of spaces
                potential_details = content.replace("\n", " ").split(" - ")
                if len(potential_details) == 4:
                    details = potential_details
                    logger.info("Used alternative parsing approach for OpenAI response")
                else:
                    logger.error(f"Invalid response format from OpenAI (expected 4 elements): {details}")
                    raise ValueError(f"Invalid response format from OpenAI (expected 4 elements): {details}")
            
            provider, date_str, usd_amount_str, currency = details
            
            # Update provider mapping if available
            if USE_PROVIDER_MAPPING:
                provider_mapper.update_from_openai_result(pdf_text, provider)
        
        # Validate date format
        try:
            date = datetime.strptime(date_str, "%d_%m_%Y")
            # Format the date back to the expected format for consistency
            date_str = date.strftime("%d_%m_%Y")
        except ValueError:
            logger.warning(f"Date format invalid: {date_str}, trying to fix...")
            # Try to fix common date format issues
            if "/" in date_str:
                parts = date_str.split("/")
                if len(parts) == 3:
                    try:
                        day, month, year = parts
                        date_str = f"{day.zfill(2)}_{month.zfill(2)}_{year}"
                        # Validate the new format
                        datetime.strptime(date_str, "%d_%m_%Y")
                        logger.info(f"Fixed date format: {date_str}")
                    except (ValueError, IndexError):
                        logger.error(f"Could not fix date format: {date_str}")
                        raise ValueError(f"Invalid date format: {date_str}")
            else:
                raise ValueError(f"Invalid date format: {date_str}")
        
        # Validate and convert USD amount
        try:
            # Remove any non-numeric characters except period
            clean_usd_amount = ''.join(c for c in usd_amount_str if c.isdigit() or c == '.')
            usd_amount = float(clean_usd_amount)
        except ValueError:
            logger.error(f"Invalid USD amount: {usd_amount_str}")
            raise ValueError(f"Invalid USD amount: {usd_amount_str}")
        
        # Validate currency
        if currency.strip().upper() != "USD":
            logger.warning(f"Currency not specified as USD: {currency}, assuming USD")
            
        # Convert USD to BRL using the configured exchange rate settings
        brl_amount = convert_usd_to_brl(usd_amount, use_live_rates, fallback_rate)
        
        # Return the extracted values
        return provider, date_str, usd_amount, brl_amount
        
    except Exception as e:
        logger.error(f"Error in OpenAI API call: {str(e)}")
        raise


def convert_usd_to_brl(usd_amount: float, 
                  use_live_rates: bool = False, 
                  fallback_rate: float = 5.74) -> float:
    """
    Convert USD amount to BRL using live rates or a fallback value.
    
    Args:
        usd_amount: Amount in USD
        use_live_rates: Whether to use live exchange rates
        fallback_rate: Fallback exchange rate to use if live rates are disabled or fail
        
    Returns:
        Equivalent amount in BRL
    """
    # Access the global logger
    global logger
    
    try:
        if use_live_rates:
            # Attempt to get the current exchange rate
            c = CurrencyRates()
            exchange_rate = c.get_rate('USD', 'BRL')
            logger.info(f"Using live exchange rate: USD 1 = BRL {exchange_rate:.2f}")
            return round(usd_amount * exchange_rate, 2)
        else:
            # Use the fallback rate
            logger.info(f"Using fallback exchange rate: USD 1 = BRL {fallback_rate:.2f}")
            return round(usd_amount * fallback_rate, 2)
    except Exception as e:
        # If there's any error, use the fallback rate
        logger.warning(f"Error getting live exchange rates: {str(e)}")
        logger.info(f"Using fallback exchange rate: USD 1 = BRL {fallback_rate:.2f}")
        return round(usd_amount * fallback_rate, 2)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by replacing/removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Replace problematic characters/phrases
    replacements = {
        'c/o': '-',  # Replace "c/o" with a hyphen
        '/': '-',    # Replace forward slashes
        '\\': '-',   # Replace backslashes
        ':': '-',    # Replace colons
        '*': '',     # Remove asterisks
        '?': '',     # Remove question marks
        '"': '',     # Remove quotes
        '<': '',     # Remove angle brackets
        '>': '',     # Remove angle brackets
        '|': '-',    # Replace pipes with hyphens
    }
    
    result = filename
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Ensure the filename doesn't have any other problematic characters
    result = "".join(c for c in result if c.isalnum() or c in "- ./_")
    
    return result.strip()


def process_file(input_file: Path, 
                 output_folder: Path, 
                 openai_model: str, 
                 use_live_rates: bool, 
                 fallback_rate: float) -> bool:
    """
    Process a single invoice PDF file.
    
    Args:
        input_file: Path to the input PDF file
        output_folder: Path to the output folder
        openai_model: OpenAI model for extraction
        use_live_rates: Flag for live exchange rates
        fallback_rate: Fallback exchange rate
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger.info(f"Processing file: {input_file.name}")
    
    try:
        # Ensure input file exists
        if not input_file.exists():
            logger.error(f"Input file does not exist: {input_file}")
            return False
            
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(input_file)
        
        # Extract invoice details using OpenAI
        provider, date_str, usd_amount, brl_amount = get_invoice_details(
            pdf_text, client, openai_model, logger, use_live_rates, fallback_rate
        )
        
        # Create new filename
        new_filename = f"{provider} - {date_str} - USD {usd_amount} - BRL {brl_amount}.pdf"
        sanitized_filename = sanitize_filename(new_filename)
        
        # Create output path
        output_file = output_folder / sanitized_filename
        
        # Check if output file already exists
        if output_file.exists():
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            output_file = output_folder / f"{sanitized_filename.replace('.pdf', '')}_{timestamp}.pdf"
            logger.warning(f"Output file already exists. Using alternative name: {output_file.name}")
        
        # Copy file to output location
        import shutil
        shutil.copy2(input_file, output_file)
        
        logger.info(f"Successfully processed: {input_file.name} → {output_file.name}")
        return True
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        return False
    except ValueError as e:
        logger.error(f"Value error processing {input_file.name}: {str(e)}")
        return False
    except PyPDF2.errors.PdfReadError as e: # Specific error for PDF reading
        logger.error(f"PDF Read error processing {input_file.name}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error processing {input_file.name}: {str(e)}", exc_info=True)
        return False


def main(input_folder: Path, 
         output_folder: Path, 
         openai_model: str, 
         use_live_rates: bool, 
         fallback_rate: float) -> None:
    """
    Main function to process all PDF invoices in the input folder.
    
    Args:
        input_folder: Path to folder containing input invoices
        output_folder: Path to folder for processed invoices
        openai_model: OpenAI model to use
        use_live_rates: Flag for live exchange rates
        fallback_rate: Fallback exchange rate
    """
    logger.info(f"Starting invoice processing")
    logger.info(f"Input folder: {input_folder}")
    logger.info(f"Output folder: {output_folder}")
    
    # Ensure folders exist
    input_folder.mkdir(exist_ok=True, parents=True)
    output_folder.mkdir(exist_ok=True, parents=True)
    
    # Track failed files
    failed_files: List[str] = []
    processed_count = 0
    skipped_count = 0
    
    # Get list of PDF files
    pdf_files = [f for f in input_folder.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
    total_files = len(pdf_files)
    
    if total_files == 0:
        logger.warning(f"No PDF files found in {input_folder}")
        return
    
    logger.info(f"Found {total_files} PDF files to process")
    
    # Process each file with tqdm progress bar
    for filepath in tqdm(pdf_files, desc="Processing Invoices", unit="file"):
        # logger.info(f"Processing file: {filepath.name}") # Redundant with tqdm
        
        if process_file(filepath, output_folder, openai_model, use_live_rates, fallback_rate):
            processed_count += 1
        else:
            failed_files.append(filepath.name)
            skipped_count += 1
    
    # Summary
    logger.info(f"\nProcessing complete: {processed_count} successful, {skipped_count} failed")
    
    if failed_files:
        logger.warning("Failed to process the following files:")
        for file in failed_files:
            logger.warning(f"- {file}")
        logger.warning("Please check these files manually.")


def validate_file(input_file: Path) -> Dict[str, Union[bool, str]]:
    """
    Validate a PDF file without processing it.
    
    Args:
        input_file: Path to the PDF file to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": False,
        "readable": False,
        "has_text": False,
        "error": None,
        "file_size": 0,
        "pages": 0
    }
    
    try:
        # Check file exists and size
        if not input_file.exists():
            result["error"] = "File does not exist"
            return result
            
        result["file_size"] = input_file.stat().st_size
        
        # Try to read PDF
        with open(input_file, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            result["pages"] = len(reader.pages)
            result["readable"] = True
            
            # Extract text to check if it has content
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text
            
            result["has_text"] = len(text.strip()) > 0
            result["valid"] = result["readable"] and result["has_text"]
            
    except Exception as e:
        result["error"] = str(e)
        
    return result


def export_results_csv(results: List[Dict], output_file: Path) -> None:
    """
    Export processing results to CSV format.
    
    Args:
        results: List of processing result dictionaries
        output_file: Path to output CSV file
    """
    if not results:
        logger.warning("No results to export")
        return
        
    fieldnames = [
        "filename", "provider", "date", "usd_amount", "brl_amount", 
        "status", "error_message", "processing_time", "output_filename"
    ]
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow({
                "filename": result.get("filename", ""),
                "provider": result.get("provider", ""),
                "date": result.get("date", ""),
                "usd_amount": result.get("usd_amount", ""),
                "brl_amount": result.get("brl_amount", ""),
                "status": result.get("status", ""),
                "error_message": result.get("error_message", ""),
                "processing_time": result.get("processing_time", ""),
                "output_filename": result.get("output_filename", "")
            })
    
    logger.info(f"Exported {len(results)} results to {output_file}")


def export_results_json(results: List[Dict], output_file: Path) -> None:
    """
    Export processing results to JSON format.
    
    Args:
        results: List of processing result dictionaries
        output_file: Path to output JSON file
    """
    if not results:
        logger.warning("No results to export")
        return
        
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "total_files": len(results),
        "successful": sum(1 for r in results if r.get("status") == "success"),
        "failed": sum(1 for r in results if r.get("status") == "failed"),
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json_module.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
    
    logger.info(f"Exported {len(results)} results to {output_file}")


def generate_processing_stats(results: List[Dict]) -> Dict:
    """
    Generate processing statistics from results.
    
    Args:
        results: List of processing result dictionaries
        
    Returns:
        Dictionary with processing statistics
    """
    if not results:
        return {}
    
    successful_results = [r for r in results if r.get("status") == "success"]
    failed_results = [r for r in results if r.get("status") == "failed"]
    
    # Provider statistics
    provider_counts = {}
    for result in successful_results:
        provider = result.get("provider", "Unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1
    
    # Amount statistics
    usd_amounts = [r.get("usd_amount", 0) for r in successful_results if isinstance(r.get("usd_amount"), (int, float))]
    brl_amounts = [r.get("brl_amount", 0) for r in successful_results if isinstance(r.get("brl_amount"), (int, float))]
    
    # Processing time statistics
    processing_times = [r.get("processing_time", 0) for r in results if isinstance(r.get("processing_time"), (int, float))]
    
    stats = {
        "summary": {
            "total_files": len(results),
            "successful": len(successful_results),
            "failed": len(failed_results),
            "success_rate": (len(successful_results) / len(results)) * 100 if results else 0
        },
        "providers": provider_counts,
        "amounts": {
            "total_usd": sum(usd_amounts),
            "total_brl": sum(brl_amounts),
            "average_usd": sum(usd_amounts) / len(usd_amounts) if usd_amounts else 0,
            "average_brl": sum(brl_amounts) / len(brl_amounts) if brl_amounts else 0,
            "max_usd": max(usd_amounts) if usd_amounts else 0,
            "min_usd": min(usd_amounts) if usd_amounts else 0
        },
        "performance": {
            "total_processing_time": sum(processing_times),
            "average_time_per_file": sum(processing_times) / len(processing_times) if processing_times else 0,
            "fastest_file": min(processing_times) if processing_times else 0,
            "slowest_file": max(processing_times) if processing_times else 0
        },
        "errors": {}
    }
    
    # Error analysis
    error_counts = {}
    for result in failed_results:
        error = result.get("error_message", "Unknown error")
        error_counts[error] = error_counts.get(error, 0) + 1
    
    stats["errors"] = error_counts
    
    return stats


def process_batch_with_stats(
    input_folder: Path, 
    output_folder: Path, 
    openai_model: str, 
    use_live_rates: bool, 
    fallback_rate: float,
    mode: str = "process"
) -> Tuple[List[Dict], Dict]:
    """
    Process batch with different modes and collect statistics.
    
    Args:
        input_folder: Path to input folder
        output_folder: Path to output folder
        openai_model: OpenAI model to use
        use_live_rates: Whether to use live exchange rates
        fallback_rate: Fallback exchange rate
        mode: Processing mode ('process', 'validate', 'dry-run')
        
    Returns:
        Tuple of (results, statistics)
    """
    logger.info(f"Starting batch processing in '{mode}' mode")
    
    # Ensure folders exist
    input_folder.mkdir(exist_ok=True, parents=True)
    if mode == "process":
        output_folder.mkdir(exist_ok=True, parents=True)
    
    # Get list of PDF files
    pdf_files = [f for f in input_folder.iterdir() if f.is_file() and f.suffix.lower() == '.pdf']
    total_files = len(pdf_files)
    
    if total_files == 0:
        logger.warning(f"No PDF files found in {input_folder}")
        return [], {}
    
    logger.info(f"Found {total_files} PDF files to process")
    
    results = []
    
    # Process each file with progress bar
    for filepath in tqdm(pdf_files, desc=f"Processing ({mode})", unit="file"):
        start_time = datetime.now()
        result = {
            "filename": filepath.name,
            "start_time": start_time.isoformat(),
            "status": "pending"
        }
        
        try:
            if mode == "validate":
                # Validation mode
                validation = validate_file(filepath)
                result.update({
                    "status": "success" if validation["valid"] else "failed",
                    "valid": validation["valid"],
                    "readable": validation["readable"],
                    "has_text": validation["has_text"],
                    "pages": validation["pages"],
                    "file_size": validation["file_size"],
                    "error_message": validation["error"]
                })
                
            elif mode == "dry-run":
                # Dry run mode - extract but don't save
                pdf_text = extract_text_from_pdf(filepath)
                provider, date_str, usd_amount, brl_amount = get_invoice_details(
                    pdf_text, client, openai_model, logger, use_live_rates, fallback_rate
                )
                
                result.update({
                    "status": "success",
                    "provider": provider,
                    "date": date_str,
                    "usd_amount": usd_amount,
                    "brl_amount": brl_amount,
                    "would_output_filename": f"{provider} - {date_str} - USD {usd_amount} - BRL {brl_amount}.pdf"
                })
                
            else:  # process mode
                # Normal processing mode
                success = process_file(filepath, output_folder, openai_model, use_live_rates, fallback_rate)
                
                if success:
                    result["status"] = "success"
                    # Try to extract the details from the output filename
                    output_files = list(output_folder.glob(f"*{filepath.stem.replace('Invoice-', '')}*.pdf"))
                    if output_files:
                        output_file = output_files[0]
                        result["output_filename"] = output_file.name
                        # Parse details from filename (basic parsing)
                        parts = output_file.stem.split(" - ")
                        if len(parts) >= 4:
                            result["provider"] = parts[0]
                            result["date"] = parts[1]
                            result["usd_amount"] = parts[2].replace("USD", "").strip()
                            result["brl_amount"] = parts[3].replace("BRL", "").strip()
                else:
                    result["status"] = "failed"
                    result["error_message"] = "Processing failed"
                    
        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            logger.error(f"Error processing {filepath.name}: {str(e)}")
        
        # Calculate processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        result["processing_time"] = processing_time
        result["end_time"] = end_time.isoformat()
        
        results.append(result)
    
    # Generate statistics
    stats = generate_processing_stats(results)
    
    return results, stats


if __name__ == "__main__":
    import argparse
    
    # --- Determine Configuration --- 
    # Precedence: CLI > Environment Variables > Defaults
    
    # Defaults
    openai_model = OPENAI_MODEL_DEFAULT
    use_live_rates = USE_LIVE_EXCHANGE_RATES_DEFAULT
    fallback_rate = FALLBACK_EXCHANGE_RATE_DEFAULT
    input_folder = DEFAULT_INPUT_FOLDER
    output_folder = DEFAULT_OUTPUT_FOLDER
    
    # Environment Variables Override Defaults
    openai_model = os.getenv("OPENAI_MODEL", openai_model)
    use_live_rates = os.getenv("USE_LIVE_EXCHANGE_RATES", str(use_live_rates)).lower() == "true"
    fallback_rate = float(os.getenv("FALLBACK_EXCHANGE_RATE", fallback_rate))
    
    # Command Line Arguments Parser
    parser = argparse.ArgumentParser(description="Process invoice PDFs using OpenAI")
    parser.add_argument("--input", "-i", type=Path, help=f"Input folder (default: {DEFAULT_INPUT_FOLDER})")
    parser.add_argument("--output", "-o", type=Path, help=f"Output folder (default: {DEFAULT_OUTPUT_FOLDER})")
    parser.add_argument("--live-rates", action="store_true", help="Use live exchange rates (overrides environment variable)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    # Advanced features
    parser.add_argument("--mode", choices=["process", "validate", "dry-run"], default="process",
                       help="Processing mode: process (normal), validate (check files only), dry-run (extract but don't save)")
    parser.add_argument("--export-csv", type=Path, help="Export results to CSV file")
    parser.add_argument("--export-json", type=Path, help="Export results to JSON file")
    parser.add_argument("--stats", action="store_true", help="Show processing statistics")
    
    args = parser.parse_args()
    
    # CLI Arguments Override Environment Variables/Defaults
    if args.input:
        input_folder = args.input
    if args.output:
        output_folder = args.output
    if args.live_rates:
        use_live_rates = True # CLI flag takes highest precedence
        
    # Set debug level AFTER parsing args
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Debug logging enabled via command line.")
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    # Log final effective settings
    logger.info(f"--- Effective Configuration ---")
    logger.info(f"Input Folder: {input_folder}")
    logger.info(f"Output Folder: {output_folder}")
    logger.info(f"Processing Mode: {args.mode}")
    logger.info(f"OpenAI Model: {openai_model}")
    logger.info(f"Use Live Exchange Rates: {use_live_rates}")
    logger.info(f"Fallback Exchange Rate: {fallback_rate}")
    logger.info(f"Export CSV: {args.export_csv}")
    logger.info(f"Export JSON: {args.export_json}")
    logger.info(f"Show Statistics: {args.stats}")
    logger.info(f"-----------------------------")

    # Process batch with statistics
    results, stats = process_batch_with_stats(
        input_folder=input_folder,
        output_folder=output_folder,
        openai_model=openai_model,
        use_live_rates=use_live_rates,
        fallback_rate=fallback_rate,
        mode=args.mode
    )
    
    # Export results if requested
    if args.export_csv:
        export_results_csv(results, args.export_csv)
    
    if args.export_json:
        export_results_json(results, args.export_json)
    
    # Show statistics if requested
    if args.stats and stats:
        logger.info("\n--- Processing Statistics ---")
        
        # Summary
        summary = stats.get("summary", {})
        logger.info(f"Total Files: {summary.get('total_files', 0)}")
        logger.info(f"Successful: {summary.get('successful', 0)}")
        logger.info(f"Failed: {summary.get('failed', 0)}")
        logger.info(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        # Provider breakdown
        providers = stats.get("providers", {})
        if providers:
            logger.info("\n--- Provider Breakdown ---")
            for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"{provider}: {count} files")
        
        # Amount statistics
        amounts = stats.get("amounts", {})
        if amounts.get("total_usd", 0) > 0:
            logger.info("\n--- Amount Statistics ---")
            logger.info(f"Total USD: ${amounts.get('total_usd', 0):.2f}")
            logger.info(f"Total BRL: R${amounts.get('total_brl', 0):.2f}")
            logger.info(f"Average USD: ${amounts.get('average_usd', 0):.2f}")
            logger.info(f"Average BRL: R${amounts.get('average_brl', 0):.2f}")
            logger.info(f"Range USD: ${amounts.get('min_usd', 0):.2f} - ${amounts.get('max_usd', 0):.2f}")
        
        # Performance statistics
        performance = stats.get("performance", {})
        if performance.get("total_processing_time", 0) > 0:
            logger.info("\n--- Performance Statistics ---")
            logger.info(f"Total Processing Time: {performance.get('total_processing_time', 0):.1f} seconds")
            logger.info(f"Average Time per File: {performance.get('average_time_per_file', 0):.1f} seconds")
            logger.info(f"Fastest File: {performance.get('fastest_file', 0):.1f} seconds")
            logger.info(f"Slowest File: {performance.get('slowest_file', 0):.1f} seconds")
        
        # Error analysis
        errors = stats.get("errors", {})
        if errors:
            logger.info("\n--- Error Analysis ---")
            for error, count in sorted(errors.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"{error}: {count} occurrences")
        
        logger.info("-----------------------------")
    
    # If not using new batch processor, fall back to original main function
    if args.mode == "process" and not args.export_csv and not args.export_json and not args.stats:
        # Use original main function for backward compatibility
        main(input_folder=input_folder, 
             output_folder=output_folder, 
             openai_model=openai_model, 
             use_live_rates=use_live_rates, 
             fallback_rate=fallback_rate) 
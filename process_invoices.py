import os
import openai
import PyPDF2
from forex_python.converter import CurrencyRates  # type: ignore
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime
import shutil

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

# Load environment variables from .env file
load_dotenv()

# Get OpenAI API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

# Set up OpenAI API client
client = OpenAI(api_key=api_key)

# Define input and output folders
input_folder = Path("input_invoices")
output_folder = Path("processed_invoices")

# Create output folder if it doesn't exist
output_folder.mkdir(exist_ok=True)

# Initialize provider mapper if available
if USE_PROVIDER_MAPPING:
    provider_mapper = ProviderMapper()
    logger.info(f"Initialized provider mapper with {len(provider_mapper.get_all_mappings())} mappings")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

# Function to interact with OpenAI for extracting invoice details
def get_invoice_details(pdf_text, provider_mapper=None):
    """Extracts invoice details, using provider mapping first if available."""
    provider_from_mapping = None
    openai_called = False # Track if OpenAI was needed

    if provider_mapper:
        provider_from_mapping = provider_mapper.identify_provider(pdf_text)
        if provider_from_mapping:
            logger.info(f"Provider identified from mapping: {provider_from_mapping}")
        else:
            logger.info("Provider not found in mapping, will use OpenAI for identification.")
            openai_called = True # OpenAI will be called for full details
    else:
        logger.warning("ProviderMapper not available, using OpenAI for all details.")
        openai_called = True # OpenAI will be called

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
        
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=100
    )
    
    # Parse the response
    content = response.choices[0].message.content.strip()
    
    # Handle parsing based on whether we used provider mapping or not
    if provider_from_mapping:
        # Parse 3 elements (date, amount, currency)
        details = content.split(" - ")
        if len(details) != 3:
            raise ValueError("Invalid response format from OpenAI (expected 3 elements)")
        
        date_str, usd_amount_str, currency = details
        provider = provider_from_mapping
    else:
        # Parse 4 elements (provider, date, amount, currency)
        details = content.split(" - ")
        if len(details) != 4:
            raise ValueError("Invalid response format from OpenAI (expected 4 elements)")
        
        provider, date_str, usd_amount_str, currency = details
        
        # Update provider mapping if available
        if USE_PROVIDER_MAPPING:
            provider_mapper.update_from_openai_result(pdf_text, provider)
    
    # Convert date string to datetime object
    date = datetime.strptime(date_str, "%d_%m_%Y")
    
    # Convert USD amount to float
    usd_amount = float(usd_amount_str)
    
    # Get BRL amount
    brl_amount = convert_usd_to_brl(usd_amount)
    
    # Return formatted string AND whether OpenAI was called for provider ID
    return f"{provider} - {date_str} - USD {usd_amount} - BRL {brl_amount}", not provider_from_mapping and openai_called

# Function to convert USD to BRL using forex-python
def convert_usd_to_brl(usd_amount: float) -> float:
    conversion_rate = float(5.74)
    return round(usd_amount * conversion_rate, 2)

def sanitize_filename(filename):
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
    
    return result.strip()

def process_file(filepath, provider_mapper=None):
    """Processes a single PDF file, returning success and if OpenAI was used for provider ID."""
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(filepath)
        
        # Extract invoice details using OpenAI
        invoice_details, openai_id_used = get_invoice_details(pdf_text, provider_mapper)
        
        # Sanitize the new filename to remove/replace invalid characters
        new_filename = sanitize_filename(f"{invoice_details}.pdf")
        new_filepath = output_folder / new_filename
        
        # Ensure we don't try to rename if the file already exists
        if new_filepath.exists():
            print(f"Warning: Output file already exists: {new_filepath}")
            # Append a number to the filename to make it unique
            base, ext = os.path.splitext(new_filename)
            counter = 1
            while True:
                new_filename = f"{base}_{counter}{ext}"
                new_filepath = output_folder / new_filename
                if not new_filepath.exists():
                    break
                counter += 1
            
        # Copy the file to the output folder
        shutil.copy2(filepath, new_filepath)
        print(f"Processed: {filepath.name} -> {new_filename}")
        return True, openai_id_used
    except Exception as e:
        print(f"Error processing {filepath}")
        print(f"Details: {str(e)}")
        return False, False # Return False for success, False for OpenAI use on error

def main():
    # Create a list to track failed files
    failed_files = []
    openai_id_calls = 0
    processed_count = 0
    
    # Initialize provider mapper if available
    mapper_instance = None
    if USE_PROVIDER_MAPPING:
        mapper_instance = ProviderMapper()
        logger.info(f"Initialized provider mapper with {len(mapper_instance.get_all_mappings())} mappings")
    else:
        logger.warning("Provider mapping disabled.")
    
    # Ensure input folder exists
    if not input_folder.exists():
        input_folder.mkdir(exist_ok=True)
        print(f"Created input folder: {input_folder}")
        print("Please place PDF invoices in this folder and run the script again.")
        return
    
    # Count PDF files in the input folder
    pdf_files = list(input_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_folder}. Please add some PDF invoices and try again.")
        return
    
    print(f"Found {len(pdf_files)} PDF files in {input_folder}")
    print(f"Processing files...")
    
    # Process each PDF file
    for filepath in pdf_files:
        print(f"Processing file: {filepath.name}")
        success, openai_used = process_file(filepath, mapper_instance)
        if success:
            processed_count += 1
            if openai_used:
                openai_id_calls += 1
        else:
            failed_files.append(filepath.name)
    
    # Summary of failed files
    if failed_files:
        print("\nFailed to process the following files:")
        for file in failed_files:
            print(f"- {file}")
        print(f"\nPlease check these files manually.")
    else:
        print("\nAll files processed successfully!")
    
    # Report mapping stats if mapper was used
    if mapper_instance:
        total_identified = processed_count # Assume each processed file needed identification
        mapping_hits = mapper_instance.hit_count
        # Note: openai_id_calls counts misses where OpenAI was *successfully* called for ID
        # mapping_misses = total_identified - mapping_hits # Can include failures before OpenAI call
        print("\n--- Provider Mapping Stats ---")
        print(f"Total Files Processed: {processed_count}")
        print(f"Providers Identified by Mapping: {mapping_hits}")
        print(f"Providers Identified by OpenAI: {openai_id_calls}")
        if total_identified > 0:
             hit_rate = (mapping_hits / total_identified) * 100
             print(f"Mapping Hit Rate: {hit_rate:.2f}%")
        else:
            print("Mapping Hit Rate: N/A (no files processed)")

    print(f"\nProcessed files have been saved to: {output_folder}")

# Run the main function
if __name__ == "__main__":
    main()

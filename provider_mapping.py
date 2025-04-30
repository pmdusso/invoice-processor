"""
Provider Mapping for Invoice Processor

This module provides functionality to identify invoice providers based on text patterns
and maintain a mapping of known providers to standardized names from a JSON file.
"""

import re
import json
import logging
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
import os
import tempfile
import shutil
from datetime import datetime

# Configure logging
logger = logging.getLogger("invoice_processor")

# Default path for provider mapping file
DEFAULT_MAPPING_FILE = Path("provider_mappings.json")

class ProviderMapper:
    """A class to handle provider name identification and standardization using a JSON file."""
    
    def __init__(self, mapping_file: Path = DEFAULT_MAPPING_FILE):
        """
        Initialize the ProviderMapper by loading mappings from the specified JSON file.

        Args:
            mapping_file: Path to the JSON file containing provider mappings.
        """
        self.mapping_file = mapping_file
        self.mappings_data: Dict[str, Any] = {}
        self.provider_mappings: List[Dict[str, Any]] = []
        self.compiled_patterns: Dict[re.Pattern, str] = {}

        self._load_mappings_from_json()
        self._compile_patterns()

    def _load_mappings_from_json(self) -> None:
        """Load provider mappings from the JSON file."""
        if not self.mapping_file.exists():
            logger.warning(f"Mapping file not found: {self.mapping_file}. Creating a default one.")
            self._create_default_mapping_file()
            # Attempt to load again after creation
            if not self.mapping_file.exists():
                 logger.error(f"Failed to create or load mapping file: {self.mapping_file}. No mappings will be available.")
                 return # Exit if file still doesn't exist

        try:
            with open(self.mapping_file, 'r') as f:
                self.mappings_data = json.load(f)
            
            # Check version
            loaded_version = self.mappings_data.get("version", "0.0.0")
            # Simple check for major version compatibility
            if not loaded_version.startswith("1."):
                logger.warning(f"Mapping file {self.mapping_file} has incompatible version '{loaded_version}'. Expected version 1.x. Attempting to load anyway.")

            # Basic validation
            if "mappings" not in self.mappings_data or not isinstance(self.mappings_data["mappings"], list):
                logger.error(f"Invalid format in mapping file {self.mapping_file}: 'mappings' array not found or not a list.")
                self.mappings_data["mappings"] = [] # Reset to empty list to avoid errors
                # Consider saving the corrected structure back
            
            self.provider_mappings = self.mappings_data.get("mappings", [])
            logger.info(f"Loaded {len(self.provider_mappings)} provider mappings from {self.mapping_file}")
            
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {self.mapping_file}: {str(e)}. No mappings loaded.")
            self.provider_mappings = [] # Ensure it's an empty list on error
        except IOError as e:
            logger.error(f"Error reading mapping file {self.mapping_file}: {str(e)}. No mappings loaded.")
            self.provider_mappings = [] # Ensure it's an empty list on error

    def _create_default_mapping_file(self) -> None:
        """Creates a default mapping file if one doesn't exist."""
        default_structure = {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "schema": {
                "description": "Provider mapping configuration file",
                "required_fields": ["pattern", "provider", "confidence", "last_used"],
                "pattern_format": "regex",
                "confidence_range": [0, 1]
            },
            "mappings": [] # Start with no default mappings, let them be learned or added manually
        }
        try:
            with open(self.mapping_file, 'w') as f:
                json.dump(default_structure, f, indent=4)
            logger.info(f"Created default mapping file at {self.mapping_file}")
        except IOError as e:
            logger.error(f"Could not create default mapping file at {self.mapping_file}: {str(e)}")

    def _compile_patterns(self) -> None:
        """Compile regex patterns from the loaded mappings for efficient matching."""
        self.compiled_patterns = {}
        for mapping in self.provider_mappings:
            pattern = mapping.get("pattern")
            provider = mapping.get("provider")
            if pattern and provider:
                try:
                    # Compile case-insensitive pattern
                    regex = re.compile(pattern, re.IGNORECASE)
                    self.compiled_patterns[regex] = provider
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}' in mapping for provider '{provider}': {str(e)}. Skipping this pattern.")
            else:
                logger.warning(f"Skipping mapping due to missing 'pattern' or 'provider': {mapping}")
        logger.debug(f"Compiled {len(self.compiled_patterns)} regex patterns.")

    def identify_provider(self, text: str) -> Optional[str]:
        """
        Try to identify the provider from the given text using compiled regex patterns.
        
        Args:
            text: The text to search for provider identifiers
            
        Returns:
            The canonical provider name if found, None otherwise
        """
        for pattern, provider in self.compiled_patterns.items():
            if pattern.search(text):
                logger.info(f"Identified provider '{provider}' using pattern matching: {pattern.pattern}")
                # Future enhancement: Update last_used timestamp here
                return provider
        return None

    def add_mapping(self, pattern: str, provider: str, confidence: float = 0.8, source: str = "learned") -> None:
        """
        Add a new provider mapping, compile the pattern, and save the updated list.
        Includes validation for the regex pattern and basic confidence range.
        
        Args:
            pattern: Regular expression pattern to match
            provider: Canonical provider name
            confidence: Confidence score (default 0.8 for learned)
            source: Source of the mapping (e.g., 'manual', 'learned')
        """
        # Avoid adding duplicates based on pattern AND provider
        for existing_mapping in self.provider_mappings:
            if existing_mapping.get("pattern") == pattern and existing_mapping.get("provider") == provider:
                logger.debug(f"Mapping for pattern '{pattern}' and provider '{provider}' already exists. Skipping add.")
                return

        # Validate pattern and confidence
        if not pattern or not provider:
            logger.warning(f"Skipping add: Pattern and provider cannot be empty.")
            return
        try:
            re.compile(pattern) # Check if pattern is a valid regex
        except re.error as e:
            logger.error(f"Invalid regex pattern provided '{pattern}': {e}. Skipping add.")
            return
        if not (0.0 <= confidence <= 1.0):
             logger.warning(f"Confidence score {confidence} out of range [0.0, 1.0]. Clamping.")
             confidence = max(0.0, min(1.0, confidence))

        new_mapping = {
            "pattern": pattern,
            "provider": provider,
            "confidence": confidence,
            "last_used": datetime.utcnow().isoformat() + "Z",
            "source": source
        }
        self.provider_mappings.append(new_mapping)
        
        # Update compiled patterns immediately
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            self.compiled_patterns[regex] = provider
            logger.info(f"Added new mapping (in memory): {pattern} -> {provider}")
            self._save_mappings_to_json()
        except re.error as e:
             logger.warning(f"Invalid regex pattern '{pattern}' for provider '{provider}': {str(e)}. Mapping added to list but not compiled.")

    def get_all_mappings(self) -> List[Dict[str, Any]]:
        """
        Get all current provider mappings (list of dictionaries).
        
        Returns:
            List of all provider mapping dictionaries.
        """
        return self.provider_mappings.copy()

    def update_from_openai_result(self, text: str, identified_provider: str) -> None:
        """
        Update mappings based on OpenAI's identification.
        This currently only updates the in-memory representation.
        
        Args:
            text: The original text that was processed
            identified_provider: The provider identified by OpenAI
        """
        # Extract potential patterns from the text
        # Simple implementation: use identified provider name itself as a pattern if found in text
        # More sophisticated logic could be added here (e.g., using parts of the name, checking context)
        escaped_provider = re.escape(identified_provider)
        if re.search(escaped_provider, text, re.IGNORECASE): 
             # Check if this exact pattern already exists for this provider
             pattern_exists = any(
                 m.get("pattern") == escaped_provider and m.get("provider") == identified_provider 
                 for m in self.provider_mappings
             )
             if not pattern_exists:
                 logger.info(f"Learned new pattern from OpenAI result: '{escaped_provider}' -> '{identified_provider}'")
                 self.add_mapping(escaped_provider, identified_provider, confidence=0.85, source="learned_openai")
             else:
                 logger.debug(f"Pattern '{escaped_provider}' for provider '{identified_provider}' already exists.")
        else:
            # Optional: Try extracting other potential keywords if direct match fails
            words = text.split()
            for word in words:
                # Example heuristic: word longer than 3 chars, present in identified_provider name
                if len(word) > 3 and word.lower() in identified_provider.lower():
                    pattern = re.escape(word)
                    pattern_exists = any(
                        m.get("pattern") == pattern and m.get("provider") == identified_provider
                        for m in self.provider_mappings
                    )
                    if not pattern_exists:
                        logger.info(f"Learned potential partial pattern from OpenAI result: '{pattern}' -> '{identified_provider}'")
                        self.add_mapping(pattern, identified_provider, confidence=0.75, source="learned_openai_partial")
                        break # Maybe only add one partial pattern per result

    # Placeholder for save method - to be implemented in the next task
    def _save_mappings_to_json(self) -> None:
        """Save the current in-memory mappings back to the JSON file using atomic operations."""
        # Create backup before saving
        backup_file = self.mapping_file.with_suffix(self.mapping_file.suffix + ".bak")
        if self.mapping_file.exists():
            try:
                shutil.copy2(self.mapping_file, backup_file)
                logger.debug(f"Created backup file: {backup_file}")
            except (IOError, OSError) as e:
                 logger.warning(f"Could not create backup file {backup_file}: {e}")

        # Ensure mappings_data is initialized (e.g., if load failed)
        if not self.mappings_data:
            self.mappings_data = {"version": "1.0.0", "schema": {}, "mappings": []}

        # Update the mappings list and last_updated timestamp
        self.mappings_data["mappings"] = self.provider_mappings
        self.mappings_data["last_updated"] = datetime.utcnow().isoformat() + "Z"

        temp_file_path = None
        try:
            # Create a temporary file in the same directory to ensure atomic move
            with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.mapping_file.parent, suffix=".tmp") as temp_f:
                temp_file_path = Path(temp_f.name)
                json.dump(self.mappings_data, temp_f, indent=4)
            
            # Atomically replace the original file with the temporary file
            shutil.move(str(temp_file_path), str(self.mapping_file))
            logger.info(f"Saved {len(self.provider_mappings)} mappings atomically to {self.mapping_file}")
            
        except (IOError, OSError) as e:
            logger.error(f"Error during atomic save to {self.mapping_file}: {str(e)}")
            # Clean up temp file if it still exists upon error
            if temp_file_path and temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except OSError as cleanup_e:
                     logger.error(f"Error cleaning up temporary file {temp_file_path}: {cleanup_e}")
        except TypeError as e:
            logger.error(f"Error serializing mappings data to JSON: {str(e)}")
            # Clean up temp file if serialization failed before move
            if temp_file_path and temp_file_path.exists():
                try:
                    os.remove(temp_file_path)
                    logger.debug(f"Cleaned up temporary file: {temp_file_path}")
                except OSError as cleanup_e:
                     logger.error(f"Error cleaning up temporary file {temp_file_path}: {cleanup_e}")

    def remove_mapping(self, pattern_to_remove: str) -> bool:
        """
        Remove a mapping based on its pattern. This currently only updates the in-memory representation.
        Saving to JSON needs to be implemented separately.
        
        Args:
            pattern_to_remove: The regex pattern string of the mapping to remove.
            
        Returns:
            True if a mapping was removed, False otherwise.
        """
        initial_length = len(self.provider_mappings)
        self.provider_mappings = [m for m in self.provider_mappings if m.get("pattern") != pattern_to_remove]
        removed_count = initial_length - len(self.provider_mappings)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} mapping(s) with pattern '{pattern_to_remove}' (in memory).")
            # Recompile patterns after removal
            self._compile_patterns()
            # Note: Need to call save method to persist this change
            self._save_mappings_to_json()
            return True
        else:
            logger.warning(f"Pattern '{pattern_to_remove}' not found in mappings.")
            return False

    def restore_from_backup(self) -> bool:
        """Restores the mapping file from the backup (.bak) file if it exists."""
        backup_file = self.mapping_file.with_suffix(self.mapping_file.suffix + ".bak")
        if not backup_file.exists():
            logger.error(f"Restore failed: Backup file not found at {backup_file}")
            return False

        try:
            shutil.copy2(backup_file, self.mapping_file)
            logger.info(f"Successfully restored mapping file from {backup_file}")
            # Reload mappings after restoring
            self._load_mappings_from_json()
            self._compile_patterns()
            return True
        except (IOError, OSError) as e:
            logger.error(f"Restore failed: Error copying backup file {backup_file} to {self.mapping_file}: {e}")
            return False

# Remove the old helper functions if they are fully replaced by class methods
# def _load_mappings(mapping_file: Path) -> Dict[str, str]: ...
# def _save_mappings(mappings: Dict[str, str]) -> None: ... 
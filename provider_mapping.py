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
        Add a new provider mapping. This currently only updates the in-memory representation.
        Saving to JSON needs to be implemented separately.
        
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
            # Note: Need to call save method to persist this change
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
                 # Note: Need to call save method to persist this change
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
                        # Note: Need to call save method to persist this change
                        break # Maybe only add one partial pattern per result

    # Placeholder for save method - to be implemented in the next task
    def _save_mappings_to_json(self) -> None:
        """Save the current in-memory mappings back to the JSON file."""
        logger.warning("_save_mappings_to_json is not yet implemented.")
        pass

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
            return True
        else:
            logger.warning(f"Pattern '{pattern_to_remove}' not found in mappings.")
            return False

# Remove the old helper functions if they are fully replaced by class methods
# def _load_mappings(mapping_file: Path) -> Dict[str, str]: ...
# def _save_mappings(mappings: Dict[str, str]) -> None: ... 
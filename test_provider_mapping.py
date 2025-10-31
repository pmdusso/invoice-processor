import unittest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from datetime import datetime
from provider_mapping import ProviderMapper

class TestProviderMapper(unittest.TestCase):
    def setUp(self):
        self.mapping_file = Path("test_mappings.json")
        if self.mapping_file.exists():
            self.mapping_file.unlink()

    def test_add_mapping(self):
        """Test adding a new mapping updates memory, file, and compiled patterns."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        self.assertEqual(len(mapper.get_all_mappings()), 0)
        self.assertEqual(len(mapper.compiled_patterns), 0)
        
        mapper.add_mapping("new_pattern", "NewProvider", confidence=0.9, source="test")
        
        # Check in-memory list
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        mapping = mapper.get_all_mappings()[0]
        self.assertEqual(mapping["pattern"], "new_pattern")
        self.assertEqual(mapping["provider"], "NewProvider")
        self.assertEqual(mapping["confidence"], 0.9)
        self.assertEqual(mapping["source"], "test")
        
        # Check compiled patterns
        self.assertEqual(len(mapper.compiled_patterns), 1)
        self.assertTrue(any(p.pattern == "new_pattern" for p in mapper.compiled_patterns.keys()))
        
        # Check file content
        self.assertTrue(self.mapping_file.exists())
        with open(self.mapping_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["mappings"]), 1)
            self.assertEqual(data["mappings"][0]["pattern"], "new_pattern")
            self.assertIn("last_updated", data)
            
    def test_add_mapping_invalid_regex(self):
        """Test adding a mapping with an invalid regex logs error and doesn't add."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        initial_mappings = len(mapper.get_all_mappings())
        with self.assertLogs(level='ERROR') as log:
            mapper.add_mapping("(", "InvalidRegexProvider") # Invalid regex
            self.assertTrue(any("Invalid regex pattern provided" in msg for msg in log.output))
        # Check it wasn't added
        self.assertEqual(len(mapper.get_all_mappings()), initial_mappings)
        self.assertEqual(len(mapper.compiled_patterns), initial_mappings)
        # Check file wasn't saved unnecessarily (or saved without the bad mapping)
        with open(self.mapping_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["mappings"]), initial_mappings)
            
    def test_add_duplicate_mapping(self):
        """Test that adding an exact duplicate pattern/provider is ignored."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        mapper.add_mapping("duplicate", "DupeProvider")
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        # Try adding again
        mapper.add_mapping("duplicate", "DupeProvider")
        # Length should remain 1
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        with open(self.mapping_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(len(data["mappings"]), 1)
            
    def test_update_from_openai_adds_new_mapping(self):
        """Test learning from OpenAI result adds a new mapping if pattern found."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        text = "Invoice from Awesome Company Ltd."
        provider = "Awesome Company Ltd."
        self.assertEqual(len(mapper.get_all_mappings()), 0)
        
        mapper.update_from_openai_result(text, provider)
        
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        mapping = mapper.get_all_mappings()[0]
        # It should escape the provider name for the pattern
        self.assertEqual(mapping["pattern"], r"Awesome\ Company\ Ltd\.") 
        self.assertEqual(mapping["provider"], provider)
        self.assertEqual(mapping["source"], "learned_openai")
        self.assertAlmostEqual(mapping["confidence"], 0.85)
        
    def test_update_from_openai_adds_partial_mapping(self):
        """Test learning adds partial mapping if full name not in text but parts are."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        text = "Bill from ACME Corp Services"
        provider = "ACME Corporation Inc."
        self.assertEqual(len(mapper.get_all_mappings()), 0)

        mapper.update_from_openai_result(text, provider)
        
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        mapping = mapper.get_all_mappings()[0]
        # Should find and escape 'ACME'
        self.assertEqual(mapping["pattern"], r"ACME") 
        self.assertEqual(mapping["provider"], provider)
        self.assertEqual(mapping["source"], "learned_openai_partial")
        self.assertAlmostEqual(mapping["confidence"], 0.75)
        
    def test_update_from_openai_does_not_add_existing(self):
        """Test learning doesn't add a mapping if it already exists."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        text = "Invoice from Awesome Company Ltd."
        provider = "Awesome Company Ltd."
        # Add manually first
        mapper.add_mapping(r"Awesome\ Company\ Ltd\.", provider, source="manual")
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        
        # Run learning - should not add a duplicate
        mapper.update_from_openai_result(text, provider)
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        # Ensure original source wasn't overwritten
        self.assertEqual(mapper.get_all_mappings()[0]["source"], "manual")

    def test_restore_from_backup(self):
        """Test restoring from a backup file."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        with self.assertLogs(level='ERROR') as log:
            restored = mapper.restore_from_backup()
            self.assertFalse(restored)
            self.assertTrue(any("Backup file not found" in msg for msg in log.output))

if __name__ == '__main__':
    unittest.main()

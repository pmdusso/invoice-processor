import unittest
import tempfile
import shutil
from pathlib import Path
import json
import os
from datetime import datetime

# Add the project root to the path to import provider_mapping
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from provider_mapping import ProviderMapper, DEFAULT_MAPPING_FILE

class TestProviderMapperJSON(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory
        self.test_dir = Path(tempfile.mkdtemp())
        self.mapping_file = self.test_dir / DEFAULT_MAPPING_FILE.name
        self.backup_file = self.mapping_file.with_suffix(self.mapping_file.suffix + ".bak")
        # Ensure no leftover files from previous tests
        if self.mapping_file.exists(): os.remove(self.mapping_file)
        if self.backup_file.exists(): os.remove(self.backup_file)

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def _create_test_file(self, content):
        """Helper to create a test mapping file."""
        with open(self.mapping_file, 'w') as f:
            json.dump(content, f, indent=4)

    def test_load_non_existent_file_creates_default(self):
        """Test that loading creates a default file if none exists."""
        self.assertFalse(self.mapping_file.exists())
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        self.assertTrue(self.mapping_file.exists())
        self.assertEqual(mapper.get_all_mappings(), [])
        with open(self.mapping_file, 'r') as f:
            data = json.load(f)
            self.assertEqual(data["version"], "1.0.0")
            self.assertIn("schema", data)
            self.assertEqual(data["mappings"], [])

    def test_load_valid_file(self):
        """Test loading a valid JSON mapping file."""
        test_data = {
            "version": "1.0.0",
            "last_updated": "2023-01-01T00:00:00Z",
            "schema": {},
            "mappings": [
                {"pattern": "test_pattern", "provider": "TestProvider", "confidence": 1.0, "last_used": "", "source": "manual"}
            ]
        }
        self._create_test_file(test_data)
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        self.assertEqual(mapper.provider_mappings[0]["pattern"], "test_pattern")
        self.assertEqual(len(mapper.compiled_patterns), 1) # Check pattern compilation

    def test_load_invalid_json(self):
        """Test loading a file with invalid JSON."""
        with open(self.mapping_file, 'w') as f:
            f.write("this is not json{")
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        # Should load with empty mappings and log an error
        self.assertEqual(mapper.get_all_mappings(), [])
        self.assertEqual(len(mapper.compiled_patterns), 0)

    def test_load_incorrect_schema_missing_mappings(self):
        """Test loading a file with incorrect schema (missing 'mappings' list)."""
        test_data = {
            "version": "1.0.0",
            "some_other_key": []
        }
        self._create_test_file(test_data)
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        # Should load with empty mappings and log an error
        self.assertEqual(mapper.get_all_mappings(), [])
        self.assertEqual(len(mapper.compiled_patterns), 0)

    def test_load_incorrect_schema_mappings_not_list(self):
        """Test loading a file where 'mappings' is not a list."""
        test_data = {
            "version": "1.0.0",
            "mappings": {"key": "value"} # Should be a list
        }
        self._create_test_file(test_data)
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        # Should load with empty mappings and log an error
        self.assertEqual(mapper.get_all_mappings(), [])
        self.assertEqual(len(mapper.compiled_patterns), 0)
        
    def test_load_incompatible_version(self):
        """Test loading a file with an incompatible version logs a warning."""
        test_data = {
            "version": "2.0.0", # Incompatible major version
            "mappings": []
        }
        self._create_test_file(test_data)
        with self.assertLogs(level='WARNING') as log:
            mapper = ProviderMapper(mapping_file=self.mapping_file)
            self.assertTrue(any("incompatible version '2.0.0'" in msg for msg in log.output))
        # Should still load the mappings
        self.assertEqual(mapper.get_all_mappings(), [])

    def test_save_creates_backup(self):
        """Test that saving correctly creates a backup file."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        # Add a mapping to trigger save
        mapper.add_mapping("save_test", "SaveProvider")
        self.assertTrue(self.mapping_file.exists())
        self.assertTrue(self.backup_file.exists())
        # Check backup content is the *previous* state (empty default file)
        with open(self.backup_file, 'r') as f:
             backup_data = json.load(f)
             self.assertEqual(len(backup_data["mappings"]), 0)
        # Check current file content
        with open(self.mapping_file, 'r') as f:
             current_data = json.load(f)
             self.assertEqual(len(current_data["mappings"]), 1)
             self.assertEqual(current_data["mappings"][0]["pattern"], "save_test")

    def test_restore_from_backup(self):
        """Test restoring the mapping file from a backup."""
        # 1. Create an initial file
        initial_data = {"version": "1.0.0", "mappings": [{"pattern": "initial", "provider": "Initial"}]}
        self._create_test_file(initial_data)
        
        # 2. Create a mapper, add data (this creates backup of initial state)
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        mapper.add_mapping("second", "SecondProvider")
        self.assertEqual(len(mapper.get_all_mappings()), 2)
        self.assertTrue(self.backup_file.exists())
        
        # 3. Check current file has 2 mappings
        with open(self.mapping_file, 'r') as f:
            current_data = json.load(f)
            self.assertEqual(len(current_data["mappings"]), 2)
            
        # 4. Restore from backup
        restored = mapper.restore_from_backup()
        self.assertTrue(restored)
        
        # 5. Check mapper reloaded initial state (1 mapping)
        self.assertEqual(len(mapper.get_all_mappings()), 1)
        self.assertEqual(mapper.provider_mappings[0]["pattern"], "initial")
        
        # 6. Check file content matches initial state
        with open(self.mapping_file, 'r') as f:
            restored_data = json.load(f)
            self.assertEqual(len(restored_data["mappings"]), 1)
            self.assertEqual(restored_data["mappings"][0]["pattern"], "initial")
            
    def test_restore_no_backup_file(self):
        """Test restore fails if no backup file exists."""
        mapper = ProviderMapper(mapping_file=self.mapping_file)
        self.assertFalse(self.backup_file.exists())
        with self.assertLogs(level='ERROR') as log:
            restored = mapper.restore_from_backup()
            self.assertFalse(restored)
            self.assertTrue(any("Backup file not found" in msg for msg in log.output))
            
if __name__ == '__main__':
    unittest.main() 
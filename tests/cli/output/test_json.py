from __future__ import annotations

import json
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

import pytest

from streamlink_cli.output import JSONOutput


class TestJSONOutput(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def _setup(self, request):
        self.output = None
        self.temp_file = BytesIO()
        
        def fin():
            if self.output:
                self.output.close()
        request.addfinalizer(fin)
        
    def test_json_output_write(self):
        self.output = JSONOutput(fd=self.temp_file, metadata={"test": "data"})
        self.output.open()
        
        # Write some test data
        self.output.write(b"test data")
        self.output.close()
        
        # Reset file position to read from the beginning
        self.temp_file.seek(0)
        
        # Read and parse the JSON lines
        lines = self.temp_file.read().decode("utf-8").strip().split("\n")
        records = [json.loads(line) for line in lines]
        
        # Should have 3 records: header, data chunk, and footer
        assert len(records) == 3
        
        # Check header
        assert records[0]["type"] == "header"
        assert records[0]["metadata"]["test"] == "data"
        assert records[0]["format"] == "json_stream"
        
        # Check data chunk
        assert records[1]["type"] == "chunk"
        assert records[1]["index"] == 0
        assert records[1]["size"] == 9  # Length of "test data"
        assert bytes.fromhex(records[1]["data"]) == b"test data"
        
        # Check footer
        assert records[2]["type"] == "footer"
        assert records[2]["chunks"] == 1
        
    def test_json_output_with_record(self):
        # Create a record output to test the record functionality
        record_file = BytesIO()
        record_output = JSONOutput(fd=record_file)
        
        # Create the main output with record
        self.output = JSONOutput(fd=self.temp_file, record=record_output)
        self.output.open()
        
        # Write some test data
        self.output.write(b"test data")
        self.output.close()
        
        # Check that the record file received the data
        record_file.seek(0)
        record_data = record_file.read()
        assert record_data != b""
        
    @patch("streamlink_cli.output.json.Path")
    def test_json_output_with_filename(self, mock_path):
        # Mock the path and file operations
        mock_file = BytesIO()
        mock_path_instance = mock_path.return_value
        mock_path_instance.open.return_value = mock_file
        mock_path_instance.parent = mock_path_instance
        
        # Create output with filename
        self.output = JSONOutput(filename=Path("test.json"))
        self.output.open()
        
        # Write some test data
        self.output.write(b"test data")
        self.output.close()
        
        # Verify the path operations
        mock_path_instance.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_path_instance.open.assert_called_once_with("wb") 
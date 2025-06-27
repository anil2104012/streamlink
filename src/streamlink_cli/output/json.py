from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import BinaryIO, Dict, Any

from streamlink_cli.compat import stdout
from streamlink_cli.output.abc import Output


log = logging.getLogger("streamlink.cli.output.json")


class JSONOutput(Output):
    """
    Output stream data in JSON format.
    
    This output module writes stream data as JSON records, with each record
    containing a chunk of base64-encoded stream data and metadata.
    """
    
    def __init__(
        self,
        filename: Path | None = None,
        fd: BinaryIO | None = None,
        record: Output | None = None,
        metadata: Dict[str, Any] | None = None,
    ):
        super().__init__()
        self.filename = filename
        self.fd = fd
        self.record = record
        self.metadata = metadata or {}
        self.chunk_index = 0
        
    def _open(self):
        if self.filename:
            self.filename.parent.mkdir(parents=True, exist_ok=True)
            self.fd = self.filename.open("wb")
            
        if self.record:
            self.record.open()
            
        # Write the header with metadata
        header = {
            "type": "header",
            "metadata": self.metadata,
            "format": "json_stream",
            "version": "1.0"
        }
        self._write_json(header)
            
    def _close(self):
        # Write footer before closing
        footer = {
            "type": "footer",
            "chunks": self.chunk_index
        }
        self._write_json(footer)
        
        if self.fd is not stdout:
            self.fd.close()
        if self.record:
            self.record.close()
            
    def _write(self, data):
        # Write the raw data to the record if specified
        if self.record:
            self.record.write(data)
            
        # Create a JSON chunk with the data
        chunk = {
            "type": "chunk",
            "index": self.chunk_index,
            "size": len(data),
            "data": data.hex()  # Use hex encoding for binary data
        }
        self._write_json(chunk)
        self.chunk_index += 1
        
        return len(data)
        
    def _write_json(self, obj):
        """Write a JSON object to the output file."""
        json_str = json.dumps(obj) + "\n"
        self.fd.write(json_str.encode("utf-8")) 
import unittest
import os
import tempfile
from tools.coding.workspace_manager import WorkspaceManager

class TestWorkspaceUIStreaming(unittest.TestCase):
    def test_01_stream_file_start_and_chunk_accumulation(self):
        ws = WorkspaceManager.get_instance()
        test_path = "src/components/Navbar.tsx"

        ws.stream_file_start(test_path)
        self.assertEqual(ws.active_file_streaming, test_path)

        ws.stream_code_chunk("import React from 'react';\n", file_path=test_path)
        ws.stream_code_chunk("export default function Navbar() {}\n", file_path=test_path)

        self.assertIn(test_path, ws.files_content)
        self.assertIn("Navbar()", ws.files_content[test_path])

    def test_02_set_final_code_persistence(self):
        ws = WorkspaceManager.get_instance()
        test_path = "src/App.tsx"
        final_code = "export default function App() { return <div>App</div>; }"

        ws.set_final_code(final_code, file_path=test_path)
        self.assertEqual(ws.files_content[test_path], final_code)

    def test_03_write_workspace_file_broadcasts(self):
        ws = WorkspaceManager.get_instance()
        with tempfile.TemporaryDirectory() as tmpdir:
            rel_file = "src/components/HeroBanner.tsx"
            code = "export default function HeroBanner() { return <section>Hero</section>; }"

            full_written = ws.write_workspace_file(tmpdir, rel_file, code)
            self.assertTrue(os.path.exists(full_written))
            self.assertEqual(ws.files_content[rel_file], code)

if __name__ == "__main__":
    unittest.main()

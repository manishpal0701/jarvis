"""
tests/test_export_approval_gate.py
Unit tests for Export Approval Gate & State Machine (Phase 4)
"""

import unittest
from unittest.mock import patch, MagicMock
from video_editing.export.export_approval_gate import (
    ExportApprovalGate,
    STATE_IDLE,
    STATE_WAITING_FOR_EXPORT_APPROVAL,
    STATE_COMPLETED,
    STATE_CANCELLED,
    STATE_EXPORT_FAILED
)


class TestExportApprovalGate(unittest.TestCase):

    def setUp(self):
        self.gate = ExportApprovalGate()

    # 1. Approval Gate Blocks Export Before Approval
    def test_01_approval_gate_blocks_before_approval(self):
        res = self.gate.request_export("Instagram ke liye export karo", r"C:\Exports\reel.mp4", overwrite=True)

        self.assertEqual(self.gate.state, STATE_WAITING_FOR_EXPORT_APPROVAL)
        self.assertFalse(self.gate.EXPORT_STARTED)
        self.assertIsNotNone(res.get("preview_summary"))
        self.assertIn("Export start karu?", res.get("preview_summary"))

    # 2. Approval Starts Export Execution
    @patch("video_editing.export.export_approval_gate.verify_output_file")
    def test_02_approval_starts_export_execution(self, mock_verify):
        mock_ctrl = MagicMock()
        mock_ctrl.export_sequence.return_value = {
            "success": True,
            "result": {"status": "COMPLETED"}
        }
        mock_verify.return_value = {
            "success": True,
            "verified": True,
            "path": r"C:\Exports\reel.mp4",
            "duration": 15.0
        }

        gate = ExportApprovalGate(controller=mock_ctrl)
        gate.request_export("Instagram ke liye export karo", r"C:\Exports\reel.mp4", overwrite=True)

        res = gate.process_approval("haan export kar do")

        self.assertTrue(gate.EXPORT_STARTED)
        self.assertEqual(gate.state, STATE_COMPLETED)
        mock_ctrl.export_sequence.assert_called_once()

    # 3. User Rejection Resets State to CANCELLED
    def test_03_user_rejection_resets_state(self):
        self.gate.request_export("Instagram ke liye export karo", r"C:\Exports\reel.mp4", overwrite=True)
        res = self.gate.process_approval("nahi, cancel karo")

        self.assertEqual(self.gate.state, STATE_CANCELLED)
        self.assertFalse(self.gate.EXPORT_STARTED)

    # 4. NOT_SUPPORTED Error Propagation
    def test_04_not_supported_error_propagation(self):
        mock_ctrl = MagicMock()
        mock_ctrl.export_sequence.return_value = {
            "success": False,
            "error": {
                "code": "NOT_SUPPORTED",
                "message": "Sequence export is not supported by current Premiere ExtendScript DOM version."
            }
        }

        gate = ExportApprovalGate(controller=mock_ctrl)
        gate.request_export("Instagram ke liye export karo", r"C:\Exports\reel.mp4", overwrite=True)
        res = gate.approve()

        self.assertEqual(gate.state, STATE_EXPORT_FAILED)
        self.assertIn("NOT_SUPPORTED", gate.last_error)


if __name__ == "__main__":
    unittest.main()

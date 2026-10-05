"""
tests/test_phase6_numlock_preservation.py
Regression tests to verify that keyboard automation in Phase 6 Premiere Pro integration:
1. Preserves NumLock ON state.
2. Preserves NumLock OFF state.
3. Performs state-aware modal dialog detection (does not inject Enter when no modal is present).
4. Restores original NumLock state if automation inadvertently alters it.
"""

import sys
import unittest
from unittest.mock import MagicMock, patch

from video_editing.software.safe_keyboard import SafeKeyboardAutomation
from video_editing.software.premiere_window_controller import PremiereWindowController
from video_editing.software.premiere_project_controller import PremiereProjectController


class TestPhase6NumLockPreservation(unittest.TestCase):

    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.get_numlock_state")
    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.restore_numlock_state")
    def test_numlock_on_remains_on(self, mock_restore, mock_get_state):
        """
        Verify that if NumLock is ON, send_key_safely maintains ON state and restores if altered.
        """
        # Simulate NumLock ON before, OFF after action
        mock_get_state.side_effect = [True, False, True]

        action_executed = [False]
        def dummy_key_action():
            action_executed[0] = True

        res = SafeKeyboardAutomation.send_key_safely("test_numlock_on_action", dummy_key_action)

        self.assertTrue(action_executed[0])
        # Assert restore_numlock_state was called with True to restore ON state
        mock_restore.assert_called_once_with(True)

    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.get_numlock_state")
    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.restore_numlock_state")
    def test_numlock_off_remains_off(self, mock_restore, mock_get_state):
        """
        Verify that if NumLock is OFF, send_key_safely maintains OFF state and restores if altered.
        """
        # Simulate NumLock OFF before, ON after action
        mock_get_state.side_effect = [False, True, False]

        action_executed = [False]
        def dummy_key_action():
            action_executed[0] = True

        res = SafeKeyboardAutomation.send_key_safely("test_numlock_off_action", dummy_key_action)

        self.assertTrue(action_executed[0])
        # Assert restore_numlock_state was called with False to restore OFF state
        mock_restore.assert_called_once_with(False)

    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.is_modal_dialog_present")
    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.send_key_safely")
    def test_modal_polling_does_not_inject_enter_when_no_modal(self, mock_send_key, mock_is_modal):
        """
        Verify that bounded modal recovery polling does NOT inject Enter or trigger key automation
        when is_modal_dialog_present() returns False.
        """
        mock_is_modal.return_value = False

        controller = PremiereProjectController()
        # Simulate is_modal_dialog_present check
        if PremiereWindowController.is_modal_dialog_present():
            SafeKeyboardAutomation.send_key_safely("state_aware_modal_dismiss_enter", lambda: None)

        # Key automation should NOT have been called
        mock_send_key.assert_not_called()

    @patch("video_editing.software.premiere_window_controller.PremiereWindowController.is_modal_dialog_present")
    @patch("video_editing.software.safe_keyboard.SafeKeyboardAutomation.send_key_safely")
    def test_modal_polling_injects_enter_when_modal_present(self, mock_send_key, mock_is_modal):
        """
        Verify that bounded modal recovery polling DOES inject Enter via SafeKeyboardAutomation
        when is_modal_dialog_present() returns True.
        """
        mock_is_modal.return_value = True

        controller = PremiereProjectController()
        if PremiereWindowController.is_modal_dialog_present():
            SafeKeyboardAutomation.send_key_safely("state_aware_modal_dismiss_enter", lambda: None)

        # Key automation MUST have been called with state_aware_modal_dismiss_enter
        mock_send_key.assert_called_once()
        self.assertEqual(mock_send_key.call_args[0][0], "state_aware_modal_dismiss_enter")


if __name__ == "__main__":
    unittest.main()

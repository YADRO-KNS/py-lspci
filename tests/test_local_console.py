import os
import unittest
from typing import TextIO
from unittest.mock import Mock, patch, MagicMock

from pylspci.consoles.local_console import LocalConsole, CommandFailed


class TestLocalConsole(unittest.TestCase):
    """
    Parent class for StandConsole test.
    """

    @classmethod
    def setUp(cls) -> None:
        """
        Run before each test.
        :return: Nothing.
        """
        mock_password = 'some_password'
        cls.logfile = MagicMock(spec=TextIO)
        cls.console = LocalConsole(password=mock_password, logfile=cls.logfile)


class TestLocalConsoleCreation(TestLocalConsole):
    """
    Tests creation of TestStandConsole.
    """

    def test_creation_success(self):
        """
        Check if creation of TestStandConsole completed.
        """
        self.assertIsInstance(self.console, LocalConsole)


class TestLocalConsoleRunCommand(TestLocalConsole):
    def test_run_command_success(self):
        """
        Check run_command against correct return values.
        """
        with patch('os.popen') as mock_popen:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures/pci_data')) as file:
                data = file.read().splitlines()
                file.seek(0)
                mock_popen.return_value = file
                result = self.console.run_command(command='some_command')
                #############################
                self.assertEqual(result, data)
                self.console.logfile.write.assert_called()
                mock_popen.assert_called_with('echo some_password|sudo -S some_command')

    def test_run_command_error(self):
        """
        Check run_command. In processing of method get Exception.
        """
        with patch('os.popen') as mock_popen:
            self.console.logfile = None
            mock_popen.return_value = Mock()
            mock_popen().close = Mock(return_value=1)
            #############################
            self.assertRaises(CommandFailed, self.console.run_command, 'some_command', '/some/path')


class TestLocalConsoleRunCommandIgnoreFail(TestLocalConsole):
    def test_run_command_ignore_fail_success(self):
        """
        Check run_command_ignore_fail against correct return values.
        """
        self.console.run_command = Mock(return_value=['some_output'])
        result = self.console.run_command_ignore_fail(command='some command')
        #############################
        self.assertEqual(result, ['some_output'])

    def test_run_command_ignore_fail_error(self):
        """
        Check run_command_ignore_fail against correct return values.
        """
        error = CommandFailed(command='some command', output=['some bad output'], exitcode=1)
        self.console.run_command = Mock(side_effect=error)
        result = self.console.run_command_ignore_fail(command='some command')
        #############################
        self.assertEqual(result, ['some bad output'])
        self.assertEqual(str(error), "Command 'some command' exited with 1. Output: ['some bad output']")

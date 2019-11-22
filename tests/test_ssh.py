import unittest
from unittest.mock import Mock, MagicMock, call, patch

from pylspci.ssh_connector import *


class TestSSHConnection(unittest.TestCase):
    """
    Parent class for ConnectorSES test.
    """

    @classmethod
    def setUpClass(cls):
        logfile = MagicMock()
        cls.ssh = SSHConnection(ip='127.0.0.1', username='test_name', password='12345678', logfile=logfile)


class TestSSHConnectionCreation(TestSSHConnection):
    def test_creation(self):
        """
        Check if creation of ConnectorSES completed.
        """
        self.assertIsInstance(self.ssh, SSHConnection)
        self.assertEqual(self.ssh.ip, '127.0.0.1')
        self.assertEqual(self.ssh.username, 'test_name')
        self.assertEqual(self.ssh.password, '12345678')
        self.assertIsNotNone(self.ssh.logfile)
        self.assertIsInstance(self.ssh.logfile, MagicMock)


class TestSSHConnectionNewClient(TestSSHConnection):
    @patch('paramiko.SSHClient', spec=paramiko.SSHClient)
    @patch('paramiko.AutoAddPolicy', return_value='MockPolicyInstance')
    def test_new_client(self, mock_policy, mock_client):
        """
        Check new Paramiko client Creation
        """
        result = self.ssh.new_client()
        self.assertIsNotNone(result)
        result.set_missing_host_key_policy.assert_called_with('MockPolicyInstance')


class TestSSHConnectionIsConnected(TestSSHConnection):
    def test_unconnected_client(self):
        """
        Check return value of unconnected client
        """
        self.ssh.paramiko_client = None
        result = self.ssh.is_connected()
        self.assertFalse(result)

    def test_is_connected_success(self):
        """
        Check against success value of paramiko transport
        """
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active = Mock(return_value=True)
        mock_client.get_transport = Mock(return_value=mock_transport)
        self.ssh.paramiko_client = mock_client

        result = self.ssh.is_connected()
        mock_client.get_transport.assert_called_once()
        mock_transport.is_active.assert_called_once()
        self.assertTrue(result)

    def test_is_connected_failure(self):
        """
        Check against failure value of paramiko transport
        """
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active = Mock(return_value=False)
        mock_client.get_transport = Mock(return_value=mock_transport)
        self.ssh.paramiko_client = mock_client

        result = self.ssh.is_connected()
        mock_client.get_transport.assert_called_once()
        mock_transport.is_active.assert_called_once()
        self.assertFalse(result)

    def test_is_connected_error(self):
        """
        Check in case of exception
        """
        mock_client = Mock()
        mock_transport = Mock()
        mock_transport.is_active = MagicMock()
        mock_transport.is_active.side_effect = Exception('Error')
        mock_client.get_transport = Mock(return_value=mock_transport)
        self.ssh.paramiko_client = mock_client

        result = self.ssh.is_connected()
        mock_client.get_transport.assert_called_once()
        mock_transport.is_active.assert_called_once()
        self.assertFalse(result)


class TestSSHConnectionTerminate(TestSSHConnection):
    def test_terminate_connected(self):
        """
        Check terminate if connection exist
        """
        mock_client = Mock()
        is_connected_mock = Mock(return_value=True)
        self.ssh.paramiko_client = mock_client
        self.ssh.is_connected = is_connected_mock

        self.ssh.terminate()
        is_connected_mock.assert_called_once()
        mock_client.close.assert_called_once()

    def test_terminate_unconnected(self):
        """
        Check terminate if there is no connection
        """
        mock_client = Mock()
        is_connected_mock = Mock(return_value=False)
        self.ssh.paramiko_client = mock_client
        self.ssh.is_connected = is_connected_mock

        self.ssh.terminate()
        is_connected_mock.assert_called_once()
        mock_client.close.assert_not_called()


class TestSSHConnectionConnect(TestSSHConnection):
    def test_connect(self):
        """
        Check connect procedure
        """
        terminate_mock = Mock()
        mock_client = Mock()
        mock_new_client = Mock(return_value=mock_client)
        self.ssh.terminate = terminate_mock
        self.ssh.new_client = mock_new_client

        self.ssh.connect()
        mock_new_client.assert_called_once()
        mock_client.connect.assert_called_with(allow_agent=False, hostname='127.0.0.1', look_for_keys=False, password='12345678', username='test_name')


class TestSSHConnectionGetConsole(TestSSHConnection):
    def test_get_console_instant_success(self):
        """
        Check successful attempt of console creation.
        """
        mock_client = Mock()
        is_connected_mock = Mock(return_value=True)
        self.ssh.paramiko_client = mock_client
        self.ssh.is_connected = is_connected_mock

        result = self.ssh._get_console()
        is_connected_mock.assert_called_once()
        self.assertEqual(result, mock_client)

    def test_get_console_success(self):
        """
        Check successful attempt of console creation after several attempts.
        """
        mock_client = Mock()
        is_connected_mock = MagicMock()
        is_connected_mock.side_effect = [False, False, True]
        mock_connect = Mock()
        self.ssh.paramiko_client = mock_client
        self.ssh.is_connected = is_connected_mock
        self.ssh.connect = mock_connect

        result = self.ssh._get_console(retry_timeout=0.1)
        is_connected_mock.assert_has_calls([call(), call(), call()])
        mock_connect.assert_has_calls([call(), call()])
        self.assertEqual(result, mock_client)

    def test_get_console_failure(self):
        """
        Check failure of console creation after several attempts.
        """
        mock_client = Mock()
        is_connected_mock = MagicMock()
        is_connected_mock.side_effect = [False, False, False, False, False]
        mock_connect = Mock()
        self.ssh.paramiko_client = mock_client
        self.ssh.is_connected = is_connected_mock
        self.ssh.connect = mock_connect

        exception = None
        try:
            self.ssh._get_console(retry_timeout=0.1, attempts=2)
        except Exception as error:
            exception = error

        is_connected_mock.assert_has_calls([call(), call(), call()])
        mock_connect.assert_has_calls([call(), call()])
        self.assertIsNotNone(exception)
        self.assertEqual(str(exception), "Cannot login via SSH")


class TestSSHConnectionRunCommand(TestSSHConnection):
    def test_run_command_success_sudo(self):
        """
        Check run_command success with sudo mode
        """
        self.ssh.username = 'test_name'
        stdin_mock = Mock()
        stdout_mock = Mock()
        stderr_mock = Mock()

        stdout_mock.channel.recv_exit_status = Mock(return_value=0)
        stdout_mock.read = Mock(return_value=b'test1\ntest2\ntest3\n')
        exec_command_mock = Mock(return_value=(stdin_mock, stdout_mock, stderr_mock))
        console_mock = Mock()
        console_mock.exec_command = exec_command_mock
        get_console_mock = Mock(return_value=console_mock)

        self.ssh._get_console = get_console_mock

        result = self.ssh.run_command(command='test command', timeout=1, sudo=True)

        self.ssh.logfile.assert_has_calls([
            call.write("test_name@127.0.0.1:~$ sudo -S -p '' test command"),
            call.write('test1'),
            call.write('test2'),
            call.write('test3'),
            call.write('test_name@127.0.0.1:~$ echo $?'),
            call.write('test_name@127.0.0.1:~$ 0')
        ])
        stdout_mock.channel.recv_exit_status.assert_called_once()
        stdout_mock.read.assert_called_once()
        console_mock.exec_command.assert_called_with(command="sudo -S -p '' test command", timeout=1)
        get_console_mock.assert_called_once()
        stdin_mock.write.assert_has_calls([call(self.ssh.password + '\n')])
        self.assertEqual(result, ['test1', 'test2', 'test3'])

    def test_run_command_success_root(self):
        """
        Check run_command success as root
        """
        self.ssh.username = 'root'

        stdin_mock = Mock()
        stdout_mock = Mock()
        stderr_mock = Mock()

        stdout_mock.channel.recv_exit_status = Mock(return_value=0)
        stdout_mock.read = Mock(return_value=b'test1\ntest2\ntest3\n')
        exec_command_mock = Mock(return_value=(stdin_mock, stdout_mock, stderr_mock))
        console_mock = Mock()
        console_mock.exec_command = exec_command_mock
        get_console_mock = Mock(return_value=console_mock)

        self.ssh._get_console = get_console_mock

        result = self.ssh.run_command(command='test command', timeout=1, sudo=True)

        self.ssh.logfile.assert_has_calls([
            call.write("root@127.0.0.1:~$ test command"),
            call.write('test1'),
            call.write('test2'),
            call.write('test3'),
            call.write('root@127.0.0.1:~$ echo $?'),
            call.write('root@127.0.0.1:~$ 0')
        ])
        stdout_mock.channel.recv_exit_status.assert_called_once()
        stdout_mock.read.assert_called_once()
        console_mock.exec_command.assert_called_with(command='test command', timeout=1)
        get_console_mock.assert_called_once()
        stdin_mock.write.assert_not_called()
        self.assertEqual(result, ['test1', 'test2', 'test3'])

    def test_run_command_failure(self):
        """
        Check run_command success as root
        """
        self.ssh.username = 'root'

        stdin_mock = Mock()
        stdout_mock = Mock()
        stderr_mock = Mock()

        stdout_mock.channel.recv_exit_status = Mock(return_value=1)
        stdout_mock.read = Mock(return_value=b'test1\ntest2\ntest3\n')
        exec_command_mock = Mock(return_value=(stdin_mock, stdout_mock, stderr_mock))
        console_mock = Mock()
        console_mock.exec_command = exec_command_mock
        get_console_mock = Mock(return_value=console_mock)

        self.ssh._get_console = get_console_mock

        exception = None
        try:
            self.ssh.run_command(command='test command', timeout=1, sudo=True)
        except Exception as error:
            exception = error

        self.ssh.logfile.assert_has_calls([
            call.write("root@127.0.0.1:~$ test command"),
            call.write('test1'),
            call.write('test2'),
            call.write('test3'),
            call.write('root@127.0.0.1:~$ echo $?'),
            call.write('root@127.0.0.1:~$ 1')
        ])
        stdout_mock.channel.recv_exit_status.assert_called_once()
        stdout_mock.read.assert_called_once()
        console_mock.exec_command.assert_called_with(command='test command', timeout=1)
        get_console_mock.assert_called_once()
        stdin_mock.write.assert_not_called()

        self.assertIsNotNone(exception)
        self.assertEqual(str(exception), "Command 'test command' exited with 1. Output: ['test1', 'test2', 'test3']")


class TestSSHConnectionRunCommandIgnoreFailure(TestSSHConnection):
    def test_run_command_ignore_failre_success(self):
        run_command_mock = Mock(return_value=['test1', 'test2', 'test3'])
        self.ssh.run_command = run_command_mock

        result = self.ssh.run_command_ignore_fail(command='test command', timeout=1, sudo=True)

        run_command_mock.assert_called_with('test command', 1, True)
        self.assertEqual(result, ['test1', 'test2', 'test3'])

    def test_run_command_ignore_failre_exception(self):
        run_command_mock = Mock()
        run_command_mock.side_effect = SSHCommandFailed(command='test command', output=['test1', 'test2', 'test3'], exitcode=1)
        self.ssh.run_command = run_command_mock

        result = self.ssh.run_command_ignore_fail(command='test command', timeout=1, sudo=True)

        run_command_mock.assert_called_with('test command', 1, True)
        self.assertEqual(result, ['test1', 'test2', 'test3'])

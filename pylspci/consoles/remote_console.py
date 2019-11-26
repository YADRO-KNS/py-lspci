import time
from typing import List, Union, TextIO

import paramiko

from .console import Console, CommandFailed


class SSHConnectionError(Exception):
    """
    Connection error occurs.
    """

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


# noinspection PyBroadException
class SSHConsole(Console):
    def __init__(self, ip: str, username: str, password: str, port: int = 22, logfile: TextIO = None):
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.logfile = logfile
        self._paramiko_client: Union[paramiko.SSHClient, None] = None

    def _new_client(self) -> paramiko.SSHClient:
        """
        Creates new instance of  connection, set its controls and return it.
        :return: Instance of paramiko client.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._paramiko_client = ssh
        return self._paramiko_client

    def is_connected(self) -> bool:
        """
        :return: Current connection state
        """
        state = False
        if self._paramiko_client is not None:
            try:
                state = self._paramiko_client.get_transport().is_active()
            except Exception:
                pass
        return state

    def connect(self) -> None:
        """
        This procedure initiate connection. Creates paramiko client if needed and connects it to target machine.
        :return: Nothing.
        """
        self.terminate()
        self._new_client().connect(
            hostname=self.ip,
            port=self.port,
            username=self.username,
            password=self.password,
            look_for_keys=False,
            allow_agent=False)

    def terminate(self):
        """
        Terminate current paramiko client session.
        :return: Nothing.
        """
        if self.is_connected():
            self._paramiko_client.close()

    def _get_console(self, attempts: int = 60, retry_timeout: Union[int, float] = 2) -> paramiko.SSHClient:
        """
        Get or create and get ssh connection.
        :param retry_timeout: Timeout between connection attempts.
        :param attempts: How many attempts of reconnection should be before Exception.
        :return: Instance of paramiko client.
        """
        counter = 0
        while not self.is_connected():
            if counter > 0:
                time.sleep(retry_timeout)
            self.connect()
            counter += 1
            if counter > attempts:
                raise SSHConnectionError("Cannot login via SSH")
        return self._paramiko_client

    def run_command(self, command: str, timeout: int = 60, sudo: bool = True, suppress_logs: bool = False) -> List[str]:
        """
        Executes command on target machine and return output as list of string.
        After execution procedure will check command exit code and will raise CommandFailed if command failed.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :param command: String with command to execute.
        :param timeout: Timeout of command execution. In case if command will not return exit code before timeout expired exception will be raised.
        :param suppress_logs: boolean flag  if set as True will suppress log output in logfile.
        :return: List of output string.
        """
        if self.username != 'root' and sudo is True:
            command = "sudo -S -p '' " + command

        if self.logfile is not None and suppress_logs is False:
            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, command)))

        stdin, stdout, stderr = self._get_console().exec_command(command=command, timeout=timeout)

        if self.username != 'root' and sudo is True:
            time.sleep(0.1)
            stdin.write(self.password + "\n")
            stdin.flush()
        exitcode: int = stdout.channel.recv_exit_status()
        output = [line.decode('utf-8') for line in stdout.read().splitlines()]

        if self.logfile is not None and suppress_logs is False:
            for line in output:
                self.logfile.write(line)

            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, 'echo $?')))
            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, exitcode)))

        if exitcode != 0:
            raise CommandFailed(command, output, exitcode)
        return output

    def run_command_ignore_fail(self, command: str, timeout: int = 60, sudo: bool = True, suppress_logs: bool = False) -> List[str]:
        """
        Executes command on target machine and return output as list of string.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :param command: String with command to execute.
        :param timeout: Timeout of command execution. In case if command will not return exit code before timeout expired exception will be raised.
        :param suppress_logs: boolean flag  if set as True will suppress log output in logfile.
        :return: List of output string.
        """
        try:
            output: List[str] = self.run_command(command, timeout, sudo, suppress_logs)
        except CommandFailed as error:
            output = error.output
        return output

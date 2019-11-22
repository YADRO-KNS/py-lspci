import time
from typing import List, Union, TextIO

import paramiko


class SSHConnectionError(Exception):
    """
    Connection error occurs.
    """

    def __init__(self, message: str) -> None:
        self.message = message

    def __str__(self) -> str:
        return self.message


class SSHCommandFailed(Exception):
    """
    Running a command failed with non-zero exit code.
    """

    def __init__(self, command: str, output: List[str], exitcode: int) -> None:
        self.command = command
        self.output = output
        self.exitcode = exitcode

    def __str__(self) -> str:
        return "Command '{command}' exited with {code}. Output: {output}".format(
            command=self.command, code=self.exitcode, output=self.output)


# noinspection PyBroadException
class SSHConnection(object):
    def __init__(self, ip: str = None, username: str = None, password: str = None, logfile: TextIO = None):
        self.ip = ip
        self.username = username
        self.password = password
        self.logfile = logfile
        self.paramiko_client: Union[paramiko.SSHClient, None] = None

    def new_client(self) -> paramiko.SSHClient:
        """
        Creates new instance of  connection, set its controls and return it.
        :return: Instance of paramiko client.
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.paramiko_client = ssh
        return self.paramiko_client

    def is_connected(self) -> bool:
        """
        :return: Current connection state
        """
        state = False
        if self.paramiko_client is not None:
            try:
                state = self.paramiko_client.get_transport().is_active()
            except Exception:
                pass
        return state

    def connect(self) -> None:
        """
        This procedure initiate connection. Creates paramiko client if needed and connects it to target machine.
        :return: Nothing.
        """
        self.terminate()
        self.new_client().connect(hostname=self.ip, username=self.username, password=self.password, look_for_keys=False, allow_agent=False)

    def terminate(self):
        """
        Terminate current paramiko client session.
        :return: Nothing.
        """
        if self.is_connected():
            self.paramiko_client.close()

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
        return self.paramiko_client

    def run_command(self, command: str, timeout: int = 60, sudo: bool = True) -> List[str]:
        """
        Executes command on target machine and return output as list of string.
        After execution procedure will check command exit code and will raise CommandFailed if command failed.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :param command: String with command to execute.
        :param timeout: Timeout of command execution. In case if command will not return exit code before timeout expired exception will be raised.
        :return: List of output string.
        """
        if self.username != 'root' and sudo is True:
            command = "sudo -S -p '' " + command

        if self.logfile is not None:
            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, command)))

        stdin, stdout, stderr = self._get_console().exec_command(command=command, timeout=timeout)

        if self.username != 'root' and sudo is True:
            time.sleep(0.1)
            stdin.write(self.password + "\n")
            stdin.flush()
        exitcode: int = stdout.channel.recv_exit_status()
        output = [line.decode('utf-8') for line in stdout.read().splitlines()]

        if self.logfile is not None:
            for line in output:
                self.logfile.write(line)

            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, 'echo $?')))
            self.logfile.write(('%s@%s:~$ %s' % (self.username, self.ip, exitcode)))

        if exitcode != 0:
            raise SSHCommandFailed(command, output, exitcode)
        return output

    def run_command_ignore_fail(self, command: str, timeout: int = 60, sudo: bool = True) -> List[str]:
        """
        Executes command on target machine and return output as list of string.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :param command: String with command to execute.
        :param timeout: Timeout of command execution. In case if command will not return exit code before timeout expired exception will be raised.
        :return: List of output string.
        """
        try:
            output: List[str] = self.run_command(command, timeout, sudo)
        except SSHCommandFailed as error:
            output = error.output
        return output

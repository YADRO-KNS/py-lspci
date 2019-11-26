import os
from typing import List

from .console import Console, CommandFailed


class LocalConsole(Console):
    def __init__(self, password: str = None):
        self.password = password

    def run_command(self, command: str, sudo: bool = True) -> List[str]:
        """
        Executes command on Local Machine and return output as list of string.
        After execution procedure will check command exit code and will raise CommandFailed if command failed.
        :param command:  String with command to execute.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :return: List of output string.
        """
        if sudo is True:
            command = 'echo %s|sudo -S %s' % (self.password, command)

        process = os.popen(command)
        output = process.read().splitlines()
        exitcode = process.close()

        if exitcode is not None:
            raise CommandFailed(command, output, (exitcode >> 8))
        else:
            return output

    def run_command_ignore_fail(self, command: str, sudo: bool = True) -> List[str]:
        """
        Executes command on Local Machine, ignores error exit codes and return output as list of string.
        :param command:  String with command to execute.
        :param sudo: Run command with sudo privileges in case if user isn't root.
        :return: List of output string.
        """
        try:
            output: List[str] = self.run_command(command=command, sudo=sudo)
        except CommandFailed as error:
            output = error.output
        return output

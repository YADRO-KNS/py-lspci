from abc import *
from typing import List


class CommandFailed(Exception):
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


class Console(ABC):
    @abstractmethod
    def run_command(self, command: str, sudo: bool = True) -> List[str]:
        pass

    @abstractmethod
    def run_command_ignore_fail(self, command: str, sudo: bool = True) -> List[str]:
        pass

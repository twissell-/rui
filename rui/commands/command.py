import logging
import traceback
from abc import (
    ABCMeta,
    abstractmethod
)


class Command(metaclass=ABCMeta):
    """Abstact class for every Command to inherit."""

    def __init__(self, **kwargs):
        super(Command, self).__init__()
        self._logger = logging.getLogger('Command.' + type(self).__name__)

    def configureParameters(self, parser):
        parser.add_argument('-v', '--verbose', action='store_true', help='Explain what it\'s being done')

        return parser

    @abstractmethod
    def _execute(self, arg_namespace):
        raise NotImplementedError

    def execute(self, arg_namespace):
        try:
            result = self._execute(arg_namespace)
            if not issubclass(type(result), CommandOutput):
                raise CommandRuntimeException('Commands "_execute" method must return "CommandOutput" object.')

            if arg_namespace.verbose:
                self._formatOutput(result)

        except CommandRuntimeException as err:
            self._logger.exception(err)
            exit(1)
        else:
            exit(result.exit_status)

    def _formatOutput(self, output):
        print(output.message)


class CommandOutput(object):
    """Data type for Command execution result."""

    def __init__(self, exit_status=0, message=''):
        super(CommandOutput, self).__init__()
        self._logger = logging.getLogger('Command.' + type(self).__name__)
        self._exit_status = exit_status
        self._message = message
        self._logger.debug('Created: ' + str(self))

    @property
    def exit_status(self):
        return self._exit_status

    @property
    def message(self):
        return self._message

    def __str__(self):
        return 'Exit Status: {exit_status}. Message: {message}'.format(
            exit_status=self._exit_status,
            message=self._message
        )


class CommandRuntimeException(Exception):
    """Base class for all Tools exceptions."""
    pass


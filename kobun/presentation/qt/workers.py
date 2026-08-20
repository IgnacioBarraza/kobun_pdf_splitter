from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    The signals live in a separate QObject because QRunnable is not a QObject
    and cannot emit them itself.
    """

    finished = Signal(object)
    failed = Signal(object)


class Worker(QRunnable):
    """
    Runs a function on Qt's thread pool and returns the result through a
    signal.

    It exists because Qt's main thread is the one repainting the window: any
    slow task running there freezes the interface. Opening a large PDF means
    reading all of it to compute its checksum, and splitting one can take
    seconds, so both go to the pool.

    The rule that never breaks: the work never touches widgets. It returns data
    through `finished` or the exception through `failed`, and the slots —which
    run on the main thread— are the only things that update the screen.
    """

    def __init__(self, operation: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self._operation = operation
        self._args = args
        self._kwargs = kwargs
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self._operation(*self._args, **self._kwargs)
        except Exception as error:
            self.signals.failed.emit(error)
        else:
            self.signals.finished.emit(result)

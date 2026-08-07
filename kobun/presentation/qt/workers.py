from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    """
    Las señales viven en un QObject aparte porque QRunnable no es un QObject
    y no puede emitirlas por sí mismo.
    """

    finished = Signal(object)
    failed = Signal(object)


class Worker(QRunnable):
    """
    Ejecuta una función en el pool de hilos de Qt y devuelve el resultado por
    señal.

    Existe porque el hilo principal de Qt es el que repinta la ventana:
    cualquier tarea lenta que corra ahí congela la interfaz. Abrir un PDF
    grande implica leerlo entero para calcular su checksum, y partirlo puede
    tardar segundos, así que ambas cosas van al pool.

    Regla que no se rompe: el trabajo nunca toca widgets. Devuelve datos por
    `finished` o la excepción por `failed`, y los slots —que corren en el hilo
    principal— son los únicos que actualizan la pantalla.
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

from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstance(QObject):
    activation_requested = Signal()

    def __init__(self, server_name: str = "DesktopTodo.V0.1") -> None:
        super().__init__()
        self.server_name = server_name
        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._receive_activation)

    def acquire_or_notify(self) -> bool:
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if socket.waitForConnected(250):
            socket.write(b"show")
            socket.waitForBytesWritten(250)
            socket.disconnectFromServer()
            return False

        QLocalServer.removeServer(self.server_name)
        return self.server.listen(self.server_name)

    def _receive_activation(self) -> None:
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.waitForReadyRead(100)
            socket.readAll()
            socket.disconnectFromServer()
        self.activation_requested.emit()


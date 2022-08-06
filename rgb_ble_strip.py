import sys
from functools import cached_property

import asyncio
import qasync

from PyQt5 import QtGui
from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QComboBox

RGB = {'Red': 255, 'Green': 255, 'Blue': 255}


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.resize(220, 117)

        self.setWindowTitle("RGB_BLEsStrip")

        self._scan_btn = QPushButton(self)
        self._scan_btn.setText('Scan')
        self._scan_btn.setGeometry(QRect(10, 10, 75, 27))

        self._connect_btn = QPushButton(self)
        self._connect_btn.setText('Connect')
        self._connect_btn.setGeometry(QRect(10, 40, 75, 27))

        self._devices_cb = QComboBox(self)
        self._devices_cb.setGeometry(QRect(90, 10, 120, 27))
        self._devices_cb.setPlaceholderText('none…')

        _label = QLabel(self)
        _label.setGeometry(QRect(90, 40, 71, 20))

        self._label = QLabel(self)
        self._label.setGeometry(QRect(90, 40, 70, 27))
        self._label.setText("Disconnected")
        self._label.setStyleSheet("QLabel {color: red; }")

        self._color_btn = QPushButton(self)
        self._color_btn.setText("Color")
        self._color_btn.setGeometry(QRect(10, 77, 80, 23))

        self._scan_btn.clicked.connect(self.ble_scan)
        self._connect_btn.clicked.connect(self.ble_connect)
        self._color_btn.clicked.connect(self.ble_send)

        self.ble_scan()

    @cached_property
    def devices(self):
        return list()

    @qasync.asyncSlot()
    async def ble_scan(self):
        pass

    @qasync.asyncSlot()
    async def ble_connect(self):
        pass

    @qasync.asyncSlot()
    async def ble_send():
        pass


def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    win = Window()
    win.show()

    with loop:
        loop.run_forever()


if __name__ == '__main__':
    main()

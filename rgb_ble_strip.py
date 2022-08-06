import sys
from functools import cached_property
from dataclasses import dataclass

import asyncio
import qasync

from PyQt5.QtCore import QObject, QRect, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QComboBox, QColorDialog

from bleak.backends.device import BLEDevice
from bleak import BleakClient, BleakScanner

rgb = {'red': 255, 'green': 255, 'blue': 255}
autoscan = True
autoconnect = True


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self._client = None

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

        if autoscan:
            self.ble_scan()

    @cached_property
    def devices(self):
        return list()

    @property
    def client(self):
        return self._client

    async def create_client(self, device):
        if self._client:
            await self._client.stop()

        self._client = QBleakClient(device)
        self._client.msg.connect(self._client.msg)
        await self._client.start()

    @qasync.asyncSlot()
    async def ble_scan(self):
        self.devices.clear()
        self._devices_cb.clear()

        self._label.setText('Scanning')
        self._label.setStyleSheet("QLabel {color: orange;}")

        devices = await BleakScanner.discover()
        self.devices.extend(devices)
        for i, device in enumerate(self.devices):
            if str(device.name).startswith('QHM'):
                self._devices_cb.insertItem(i, device.name, device)

        if len(devices) > 0:
            self._devices_cb.setCurrentIndex(0)

            self._label.setText('Found!')
            self._label.setStyleSheet("QLabel {color: green;}")
        else:
            self._label.setText('No devices!')
            self._label.setStyleSheet("QLabel {color: red;}")

        if len(devices) == 1 and autoconnect:
            self.ble_connect()

    @qasync.asyncSlot()
    async def ble_connect(self):
        self._label.setText('Connecting')
        self._label.setStyleSheet("QLabel {color: orange;}")

        device = self._devices_cb.currentData()
        if isinstance(device, BLEDevice):
            await self.create_client(device)
            self._label.setText('Connected')
            self._label.setStyleSheet("QLabel {color: green;}")
            self._scan_btn.setEnabled(False)
            self._connect_btn.setEnabled(False)

    @qasync.asyncSlot()
    async def ble_send(self):
        global rgb

        rgb = ColorSelector().color()
        await self.client.write()


class ColorSelector(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle('Color Selector')
        self.setGeometry(100, 100, 500, 400)
        self.UiComponents()
        self.show()

    def UiComponents(self):
        color = QColorDialog.getColor()

        rgb['red'] = color.red()
        rgb['green'] = color.green()
        rgb['blue'] = color.blue()

        return rgb

    def color(self):
        return rgb


@dataclass
class QBleakClient(QObject):
    device: BLEDevice
    msg = pyqtSignal(bytes)

    def __post_init__(self):
        super().__init__()

        self.UART_SERVICE_UUID = None
        self.UART_RX_CHAR_UUID = None
        self.UART_TX_CHAR_UUID = None
        self.UART_SAFE_SIZE = 20

    @cached_property
    def client(self) -> BleakClient:
        return BleakClient(self.device, disconnected_callback=self.disconnect)

    async def start(self):
        await self.client.connect()
        services = await self.client.get_services()

        for item in services.characteristics:
            if services.characteristics[item].properties[0] == 'write-without-response' and not self.UART_TX_CHAR_UUID:
                self.UART_TX_CHAR_UUID = services.characteristics[item].uuid
            elif services.characteristics[item].properties[0] == 'read' and not self.UART_RX_CHAR_UUID:
                self.UART_RX_CHAR_UUID = services.characteristics[item].uuid

    async def stop(self):
        await self.client.disconnect()

    async def write(self):
        lst = [86, rgb['red'], rgb['green'], rgb['blue'],
               (int(10*255/100) & 0xFF), 256-16, 256-86]

        values = bytearray(lst)

        try:
            await self.client.write_gatt_char(self.UART_TX_CHAR_UUID, values, False)
        except Exception as e:
            print(e)

    def disconnect(self):
        for task in asyncio.all_tasks():
            task.cancel()

        print('Device disconnected.')

    def read(self, data: bytearray):
        self.msg.emit(data)
        print('received: ', data)


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

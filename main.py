from mimetypes import init
from evdev import InputDevice, categorize, ecodes, list_devices
from os import environ
from time import sleep, time
import logging
import asyncio
import subprocess as sp


class Bluetooth2HID:
    def __init__(
        self,
        input_device_path: str = "/dev/input/event21",
        hid_device: str = "/dev/hidg0",
    ) -> None:
        """Initialize the Bluetooth2HID class"""
        self.logger = logging.getLogger("Bluetooth2HID")
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.INFO)

        self.logger.info(
            f"Starting Bluetooth2HID instance with device {input_device_path}"
        )
        self.list_evdev_devices()
        self.input_device = input_device_path
        self.hid_device = hid_device
        self.device = self.open_input_device()

        if self.device:
            self.capture_input_events()

    def list_evdev_devices(self) -> list:
        """List currently connected evdev devices"""
        devices = [InputDevice(path) for path in list_devices()]
        for device in devices:

            # gotta be a better way to do this
            if "Keyboard" in device.name and "input" in device.phys:
                self.logger.info(
                    f"Path: {device.path} Name: {device.name} Phys: {device.phys}"
                )

    async def print_device_events(self, dev):
        async for ev in dev.async_read_loop():
            print(repr(ev))

    def capture_input_events(self):
        self.logger.info(f"Capturing input events for device {self.device.name}")
        if self.device:
            self.loop = asyncio.get_event_loop()
            self.loop.run_until_complete(self.print_device_events(self.device))

    def open_input_device(self) -> InputDevice:
        """Attempts to open the input device at self.device_path"""
        start_time = time()
        device = None

        while not device:
            try:
                device = InputDevice(self.input_device)
                if device:
                    # device.grab()
                    self.logger.info(
                        f"Grabbed device at {self.input_device}: {device.name}"
                    )

                    return device

            except OSError as ex:
                print(ex)
                self.logger.info(f"Running processes on the device")
                sp.run(["sudo", "fuser", "-v", self.input_device])
                sleep(1)
                # try for five seconds
                # then fail if device can't be found or captured
                # if time() - start_time > 5:
                #     self.logger.error("Failed to open device after 5 retries.. exiting")
                #     break

    def send_keys(self, packet) -> None:
        """Send a HID packet to the hid device"""


if __name__ == "__main__":
    b = Bluetooth2HID()

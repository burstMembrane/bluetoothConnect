#!/usr/bin/env python3

import bluetooth
import json
from halo import Halo
from bluetooth.btcommon import BluetoothError
from time import sleep

import subprocess as sp
from argparse import ArgumentParser

config = json.load(open("config.json"))
device_name = config["deviceName"]


def join_values(key, arr: list = []):
    """join a list of returned values to a single string with a coimma delimiter"""
    return ", ".join([str(d[key]) for d in arr])


def check_process_code(process: sp.CompletedProcess):
    """Check a processes return code and return a value"""


def connect(address: str = "", max_retries: int = 5):
    """Connect to a bluetooth device based on MAC address"""

    spinner = Halo(
        text=f"Waiting for device at address {address}",
        spinner="dots",
        color="red",
    )
    spinner.start()
    spinner.text = f"Attempting to connect to device at address {address}"
    if not address:
        spinner.fail("address not provided... exiting")
        return
    name = False
    name_retries = 0

    while not name:
        try:
            spinner.text = f"Scanning for BT device at {address}"
            name = bluetooth.lookup_name(address)
            if not name:
                spinner.stop()

                name_retries += 1
                spinner.warn(
                    f"Device not found.. retrying [{name_retries}/{max_retries}]"
                )
                spinner.start()
                if name_retries >= max_retries:
                    spinner.fail(
                        f"Failed to find device after {max_retries} retries... exiting"
                    )
                    return
                sleep(1)
            else:
                spinner.succeed(f"Found device {name} on address {address}")
                spinner.stop()
        except Exception as e:
            spinner.fail(f"Failed with error: {e}")
            return

        except KeyboardInterrupt:
            spinner.info(f"Received interrupt.. exiting.")
            return
    spinner.text = f"Connecting to {name}"

    spinner.start()
    service = bluetooth.find_service(address=address)

    if not service:
        spinner.fail(f"Couldn't find service info for address {address}.. exiting")

    connected = False

    trusted = 0
    paired = 0
    connect_retries = 0

    while not connected:
        try:
            if not trusted:
                spinner.info(f"Trusting device: {name}")
                trust = sp.run(
                    ["bluetoothctl", "--", "trust", address],
                    text=True,
                    capture_output=True,
                )
                trusted = True if trust.returncode == 0 else False
                if trusted:
                    spinner.succeed(f"Device {address} is trusted")
            if not paired:
                spinner.info(f"Pairing device: {name}")
                paired_devices = sp.run(
                    ["bluetoothctl", "--", "paired-devices"],
                    text=True,
                    capture_output=True,
                )
                if address in paired_devices.stdout:
                    spinner.warn(f"Device {name} is already paired")
                    paired = True
                if not paired:
                    pair = sp.run(
                        ["bluetoothctl", "--", "pair", address],
                        text=True,
                        capture_output=True,
                    )
                    print(pair.stdout)

                    if "org.bluez.Error.AlreadyExists" in pair.stdout:
                        spinner.warn(f"Device {name} is already paired")
                        paired = True
                    paired = True if pair.returncode == 0 else False
                    if paired:
                        spinner.succeed(f"Device {name} paired successfully")
            if not connected:
                connect = sp.run(
                    ["bluetoothctl", "--", "connect", address],
                    text=True,
                    capture_output=True,
                )
                connected = True if connect.returncode == 0 else False
                connect_retries += 1
                if connected:
                    spinner.succeed(f"Device {address} is connected! ")
                    break
                else:
                    spinner.fail("Connection failed: retrying in 5s")

            # if we fail.. wait for 1s then try again
            sleep(1)
        except Exception as e:
            spinner.fail(e)
            sleep(1)

    info = sp.run(
        ["bluetoothctl", "--", "info", address], text=True, capture_output=True
    )
    print(info.stdout.split("\n\t")[1:])

    spinner.stop()
    return


def scan_for_device(
    device_name: str = "", address: str = "", retry_limit: int = 5, duration: int = 10
):

    """Scans for a bluetooth device by name and returns it's host address"""
    retries = 0
    spinner = Halo(
        text=f"Scanning for device {device_name}", spinner="dots", color="green"
    )

    found = False
    invalid_devices = []

    while not found and retries < retry_limit:
        spinner.start()
        try:
            devices = bluetooth.discover_devices(
                duration=duration,
                lookup_names=True,
            )
        except BluetoothError as e:
            spinner.fail(e)
            spinner.fail(f"Bluetooth error: retrying in 5s...")
            sleep(5)

        num_devices = len(devices)
        if not num_devices:
            spinner.warn(f"No devices found.. attempt {retries} of {retry_limit}")
            retries += 1

        if num_devices > 0:
            spinner.info(f"Found {num_devices} devices.")
            for addr, name in devices:
                spinner.info(f"{name}:{addr}")
                if address and address == addr or name and name in device_name:
                    spinner.succeed(f"Found device at address {addr} with name {name}")
                    return addr
                else:
                    invalid_devices.append({name, addr})

    spinner.stop()
    spinner.fail(f"Device {device_name} not found after {retries} retries.. exiting")
    return


def scan_devices(duration: int = 20):
    """Scan for nearby bluetooth devices and return their names and addresses"""

    from time import time

    devices = []
    start_time = time()

    while time() - start_time < duration:
        spinner = Halo(
            text=f"Scanning nearby bluetooth devices 📶",
            spinner="dots",
        )
        spinner.start()

        try:
            scanned_devices = bluetooth.discover_devices(lookup_names=True)
        except BluetoothError as e:

            spinner.fail(f"Bluetooth error: retrying in 5s...")
            sleep(5)

        if not scanned_devices:
            spinner.warn(f"No devices found")
            spinner.stop()

        for device in scanned_devices:
            if device not in devices:
                name, addr = device
                spinner.info(f"Found device {name}: {addr}")
                devices.append(device)

        spinner.stop()

    spinner.info(
        f"Found {len(devices)} device{'s' if len(devices) > 1 else ''} in {round(time() - start_time,2)}s"
    )
    for i, device in enumerate(devices):
        addr, name = device
        spinner.clear()
        spinner.succeed(f"    [{i}] Name: {name}  Address: {addr}")
    return list(set(devices))


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("-s", "--scan", action="store_true")
    parser.add_argument(
        "-t",
        "--time",
        type=int,
        default=30,
        help="Amount of time to run scan for. Default is 30s",
    )
    parser.add_argument(
        "-n", "--name", type=str, default="", help="Device name or string to scan for"
    )
    parser.add_argument(
        "-a",
        "--address",
        type=str,
        default="",
        help="Bluetooth MAC address to connect to: XX:XX:XX:XX:XX:XX",
    )
    parser.add_argument(
        "-c",
        "--connect",
        action="store_true",
        help="Pair, trust and connect to Bluetooth device with a given address",
    )
    parser.add_argument(
        "-i",
        "--info",
        action="store_true",
        help="Scan for a specific bluetooth device with a given address or name",
    )
    parser.add_argument(
        "-r",
        "--retries",
        type=int,
        default=5,
        help="The number of reconnection attempts that should be made before xit if a device is not found. Default 5",
    )
    opts = parser.parse_args()
    if opts.scan:
        devices = scan_devices(opts.time)
    if opts.info:
        addr = scan_for_device(
            name=opts.name,
            address=opts.address,
            duration=opts.time,
            retry_limit=opts.retries,
        )
    if opts.connect:
        result = connect(address=opts.address, max_retries=opts.retries)

#!/usr/bin/env python3
"""JLab Linux Controller - Command Line Interface for Scripting and Hotkeys."""

import argparse
import sys
import time
from jlab_controller.bluetooth.discovery import BluetoothScanner
from jlab_controller.constants import AncMode, EqPreset
from jlab_controller.core.device import JLabDevice

def parse_args():
    parser = argparse.ArgumentParser(
        description="JLab Headphone Linux Controller CLI - Control EQ, ANC, and Hardware settings from bash/hotkeys."
    )
    parser.add_argument("--device", "-d", type=str, help="Device MAC Address (e.g. DC:A8:00:60:77:F7)")
    parser.add_argument("--list", "-l", action="store_true", help="List detected JLab Bluetooth devices")
    parser.add_argument("--status", "-s", action="store_true", help="Query and print current headphone status")
    parser.add_argument(
        "--set-anc",
        choices=["on", "aware", "off"],
        help="Set Noise Control mode: 'on' (ANC), 'aware' (Be Aware), or 'off'",
    )
    parser.add_argument("--set-awareness", type=int, help="Set Be Aware transparency volume level (0-100)")
    parser.add_argument(
        "--set-eq",
        choices=["signature", "balanced", "bass_boost", "custom"],
        help="Switch EQ Preset",
    )
    parser.add_argument(
        "--set-gains",
        type=str,
        help="Set 10-band EQ gains in dB separated by commas (e.g. '1,1,0,-2,-3,-4,-4,-2,-1,-2')",
    )
    parser.add_argument("--set-wear", choices=["on", "off"], help="Enable/disable in-ear auto-pause sensor")
    parser.add_argument("--set-latency", choices=["on", "off"], help="Enable/disable low-latency movie/game mode")
    return parser.parse_args()

def main():
    args = parse_args()

    # 1. List devices
    devices = BluetoothScanner.get_paired_jlab_devices()
    if args.list:
        print("Detected Bluetooth Devices:")
        for d in devices:
            print(f"  - {d.name} ({d.address}) | Connected: {d.connected} | Battery: {d.battery}%")
        return

    # Select target device
    target_addr = args.device
    if not target_addr:
        if not devices:
            print("Error: No JLab or connected Bluetooth devices found in BlueZ.", file=sys.stderr)
            sys.exit(1)
        target_addr = devices[0].address
        print(f"Using device: {devices[0].name} ({target_addr})")

    device = JLabDevice(target_addr)
    print(f"Connecting to {target_addr}...")
    if not device.connect():
        print(f"Error: Could not connect to {target_addr} over RFCOMM.", file=sys.stderr)
        sys.exit(1)

    time.sleep(0.3)

    # Handle actions
    if args.set_anc:
        anc_map = {"on": AncMode.ANC_ON, "aware": AncMode.BE_AWARE, "off": AncMode.OFF}
        mode = anc_map[args.set_anc]
        device.set_anc_mode(mode)
        print(f"✓ ANC set to: {mode.value}")

    if args.set_awareness is not None:
        device.set_awareness_level(args.set_awareness)
        print(f"✓ Be Aware transparency level set to: {args.set_awareness}%")

    if args.set_eq:
        eq_map = {
            "signature": EqPreset.SIGNATURE,
            "balanced": EqPreset.BALANCED,
            "bass_boost": EqPreset.BASS_BOOST,
            "custom": EqPreset.CUSTOM,
        }
        preset = eq_map[args.set_eq]
        device.set_eq_preset(preset)
        print(f"✓ EQ Preset set to: {args.set_eq}")

    if args.set_gains:
        try:
            gains = [float(x.strip()) for x in args.set_gains.split(",")]
            if len(gains) != 10:
                print("Error: Expected exactly 10 comma-separated gain values for 10-band EQ.", file=sys.stderr)
                sys.exit(1)
            device.set_custom_eq_gains(gains)
            print(f"✓ Custom 10-band EQ gains applied: {gains}")
        except ValueError:
            print("Error: Invalid gain format. Use numeric values separated by commas.", file=sys.stderr)
            sys.exit(1)

    if args.set_wear:
        val = args.set_wear == "on"
        device.set_wear_detection(val)
        print(f"✓ Auto-pause wear detection set to: {val}")

    if args.set_latency:
        val = args.set_latency == "on"
        device.set_low_latency_mode(val)
        print(f"✓ Low-latency movie mode set to: {val}")

    if args.status or len(sys.argv) == 1:
        device.refresh_status()
        time.sleep(0.2)
        print("\n--- JLab Device Status ---")
        print(f"Device: {device.name} [{device.address}]")
        print(f"Connected: {device.is_connected}")
        print(f"Battery: {device.battery_level}%")
        print(f"ANC Mode: {device.anc_mode.value}")
        print(f"Awareness Level: {device.awareness_level}%")
        print(f"EQ Preset: {device.eq_preset}")

    device.disconnect()

if __name__ == "__main__":
    main()

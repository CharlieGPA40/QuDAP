import pyvisa
import time


def categorize_instrument(resource_name):
    """Determine the connection type from resource string"""
    if "GPIB" in resource_name:
        return "GPIB"
    elif "USB" in resource_name:
        return "USB"
    elif "TCPIP" in resource_name:
        return "Ethernet/LAN"
    elif "ASRL" in resource_name:
        return "Serial"
    elif "PXI" in resource_name:
        return "PXI"
    else:
        return "Other"


def query_instrument_id(inst):
    """
    Try multiple identification commands to support various instruments
    Returns: (id_string, command_used)
    """

    # List of common identification commands
    id_commands = [
        "*IDN?",  # Standard SCPI (most modern instruments)
        "ID?",  # Older instruments like SR830, DSP7265
        "ID",  # Some instruments without "?"
        "*ID?",  # Some HP/Agilent instruments
        "IDENTIFY?",  # Some custom implementations
        "MODEL?",  # Some older instruments
        "I",  # Very old instruments
        "++ver",  # Prologix GPIB-USB controllers
    ]

    for cmd in id_commands:
        try:
            # Try to query with this command
            response = inst.query(cmd).strip()

            # Check if we got a valid response
            if response and len(response) > 0:
                return (response, cmd)

        except pyvisa.errors.VisaIOError:
            # This command didn't work, try next one
            continue
        except Exception as e:
            # Some other error, continue
            continue

    # If none of the queries worked, try write-only commands
    write_commands = [
        ("V", "Firmware version request"),  # Some instruments
    ]

    for cmd, description in write_commands:
        try:
            inst.write(cmd)
            time.sleep(0.1)  # Wait for response
            response = inst.read().strip()
            if response:
                return (response, cmd)
        except:
            continue

    return (None, None)


def detect_all_instruments(timeout=2000, verbose=False):
    """
    Detect instruments across all connection types with support for various ID commands

    Args:
        timeout: Timeout in milliseconds for each instrument query
        verbose: Show detailed information about query attempts
    """

    rm = pyvisa.ResourceManager()
    print(f"VISA Backend: {rm}")

    try:
        # Get all resources
        resources = rm.list_resources()

        if not resources:
            print("No instruments found!")
            return

        # Organize by connection type
        instruments_by_type = {
            "GPIB": [],
            "USB": [],
            "Ethernet/LAN": [],
            "Serial": [],
            "PXI": [],
            "Other": []
        }

        for resource in resources:
            conn_type = categorize_instrument(resource)

            instrument_info = {
                "resource": resource,
                "id": "Unknown",
                "command": None,
                "status": "Not responding"
            }

            if verbose:
                print(f"Trying {resource}...")

            try:
                # Connect to instrument
                inst = rm.open_resource(resource)
                inst.timeout = timeout

                # Set read/write termination (helps with some instruments)
                try:
                    inst.read_termination = '\n'
                    inst.write_termination = '\n'
                except:
                    pass

                # Try to identify the instrument
                idn, cmd_used = query_instrument_id(inst)

                if idn:
                    instrument_info["id"] = idn
                    instrument_info["command"] = cmd_used
                    instrument_info["status"] = "Connected"

                    if verbose:
                        print(f"  ✓ Responded to '{cmd_used}': {idn}")
                else:
                    instrument_info["status"] = "Connected (No ID response)"
                    if verbose:
                        print(f"  ✗ No valid ID response")

                inst.close()

            except Exception as e:
                instrument_info["status"] = f"Error: {str(e)[:50]}"
                if verbose:
                    print(f"  ✗ Error: {e}")

            instruments_by_type[conn_type].append(instrument_info)

        # Display results organized by connection type
        total_found = 0

        for conn_type in ["GPIB", "USB", "Ethernet/LAN", "Serial", "PXI", "Other"]:
            instruments = instruments_by_type[conn_type]

            if instruments:
                for inst in instruments:
                    print(f"\nResource: {inst['resource']}")
                    print(f"Status:   {inst['status']}")
                    if inst['status'] == "Connected":
                        print(f"ID Cmd:   {inst['command']}")
                        print(f"ID:       {inst['id']}")
                        total_found += 1
                    elif inst['status'] == "Connected (No ID response)":
                        print(f"Note:     Instrument connected but doesn't respond to ID queries")
                        total_found += 1

        # Summary
        print("\n" + "=" * 70)
        print(f"Summary: {total_found} instrument(s) responding")
        print("=" * 70)

        return instruments_by_type

    except Exception as e:
        print(f"Error during detection: {e}")
        return None


def instrument_commands(resource_name, custom_commands=None):
    """
    Test which identification commands work with a specific instrument

    Args:
        resource_name: VISA resource string (e.g., "GPIB0::10::INSTR")
        custom_commands: Optional list of additional commands to try
    """

    rm = pyvisa.ResourceManager()

    # Default commands to test
    test_commands = [
        "*IDN?", "ID?", "ID", "*ID?", "IDENTIFY?",
        "MODEL?", "I", "++ver", "VER?", "VERSION?"
    ]

    # Add custom commands if provided
    if custom_commands:
        test_commands.extend(custom_commands)

    print(f"\n{'=' * 70}")
    print(f"Testing Commands: {resource_name}")
    print(f"{'=' * 70}\n")

    try:
        inst = rm.open_resource(resource_name)
        inst.timeout = 2000

        try:
            inst.read_termination = '\n'
            inst.write_termination = '\n'
        except:
            pass

        working_commands = []

        for cmd in test_commands:
            try:
                response = inst.query(cmd).strip()
                if response:
                    print(f"✓ '{cmd}' → {response}")
                    working_commands.append((cmd, response))
                else:
                    print(f"✗ '{cmd}' → (empty response)")
            except Exception as e:
                print(f"✗ '{cmd}' → Error: {str(e)[:40]}")

        inst.close()

        print(f"\n{'─' * 70}")
        print(f"Working commands: {len(working_commands)}")
        if working_commands:
            print("\nRecommended command:", working_commands[0][0])

    except Exception as e:
        print(f"Error connecting: {e}")


def add_custom_instrument_support():
    """
    Example: Add support for custom/proprietary instruments
    Returns a dictionary of instrument-specific commands
    """

    custom_instruments = {
        # Format: "Manufacturer Model": ["command1", "command2", ...]
        "Signal Recovery ": ["ID?", "ID"],
        "Stanford Research": ["ID?", "*IDN?"],
        'Keithley': ["ID?", "*IDN?"],
        "HP/Agilent (old)": ["*ID?", "ID?"],
        "Tektronix Oscilloscopes": ["*IDN?", "ID?"],
        "Custom Instrument": ["STATUS?", "INFO?", "WHOAMI?"],
    }

    return custom_instruments


if __name__ == "__main__":
    # Method 1: Auto-detect all instruments with multiple ID command support
    print("Auto-detecting instruments...\n")
    instruments = detect_all_instruments(verbose=False)
    print(instruments)
    # Method 2: Test specific instrument with all commands (uncomment to use)
    # instrument_commands("GPIB0::12::INSTR")

    # Method 3: Test with custom commands
    # instrument_commands("GPIB2::24::INSTR", custom_commands=["MYID?", "STATUS?"])

    # Show supported custom instruments
    # print("\n" + "=" * 70)
    # print("Known Instrument-Specific Commands:")
    # print("=" * 70)
    # custom = add_custom_instrument_support()
    # for instrument, commands in custom.items():
    #     print(f"{instrument}: {', '.join(commands)}")
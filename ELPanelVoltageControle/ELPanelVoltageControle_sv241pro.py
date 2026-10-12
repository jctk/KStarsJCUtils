#!/usr/bin/env python3
"""
Script for capturing flat frames
- Adjusts the EL panel voltage during flat frame capture based on the filter type.
- Determines the voltage of the SV241 Pro's Variable DC Port according to the filter type.

"""

import sys
import json
import subprocess

def main():
    try:
        # Read JSON data from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract script type and job information
        script_type = input_data.get("script_type", "")
        job = input_data.get("job", {})
        frame_type = job.get('type', 'Unknown')
        filter_type = job.get('filter', 'None')

        # Log basic job information
        print(f"Script type={script_type} Target={job.get('target_name', 'Unknown')} Frame type={frame_type} Filter={filter_type}")

        # Handle different script types
        match script_type:
            case "PRE_CAPTURE":
                # Adjust the EL panel voltage during flat frame capture based on the filter type.
                if frame_type == "Flat":
                    # Check if SV241 Pro is running.
                    result = subprocess.run(["indi_eval", '"SVBONY SV241 Pro.CONNECTION.CONNECT"==1'])
                    if result.returncode == 0:
                        print("SV241 Pro driver is connected.")

                        # Determine the voltage of the SV241 Pro's Variable DC Port according to the filter type.
                        voltage = 6 if filter_type == "B" or filter_type == "L" or filter_type == "UVIRcut" else 12
                        print(f"SV241 Pro Voltage: {voltage}V for '{filter_type}'")

                        # Variable DC Port On
                        result = subprocess.run(["indi_setprop", "SVBONY SV241 Pro.VARIABLE_CHANNELS.VAR_CHANNEL_1=On"])
                        if result.returncode != 0:
                            print("Failed to turn on SV241 Pro Variable DC Port.", file=sys.stderr)
                            sys.exit(1)

                        # Variable DC Port set voltage
                        result = subprocess.run(["indi_setprop", f"SVBONY SV241 Pro.VARIABLE_VOLTAGES.VAR_CHANNEL_1={voltage}"])
                        if result.returncode != 0:
                            print("Failed to set SV241 Pro Variable DC Port voltage.", file=sys.stderr)
                            sys.exit(1)
                    else:
                        print("SV241 Pro driver is not connected.", file=sys.stderr)
                        sys.exit(1)

                elif frame_type == "Dark":
                    # Check if SV241 Pro is running.
                    result = subprocess.run(["indi_eval", '"SVBONY SV241 Pro.CONNECTION.CONNECT"==1'])
                    if result.returncode == 0:
                        # Variable DC Port Off
                        result = subprocess.run(["indi_setprop", "SVBONY SV241 Pro.VARIABLE_CHANNELS.VAR_CHANNEL_1=Off"])
                        if result.returncode != 0:
                            print("Failed to turn off SV241 Pro Variable DC Port.", file=sys.stderr)
                            sys.exit(1)

            case "POST_CAPTURE":
                pass  # Valid script types, continue processing
            case "PRE_JOB":
                pass  # Valid script types, continue processing
            case "POST_JOB":
                pass  # Valid script types, continue processing
            case _:
                print(f"Unknown script type: {script_type}", file=sys.stderr)

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
    
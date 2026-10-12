#!/usr/bin/env python3
"""
Example Ekos Capture Script

This script demonstrates how to read and process JSON data
passed from Ekos during capture script execution.
"""

import sys
import json

def main():
    try:
        # Read JSON data from stdin
        input_data = json.loads(sys.stdin.read())

        # Extract script type and job information
        script_type = input_data.get("script_type", "")
        job = input_data.get("job", {})

        # Log basic job information
        print(f"Script type: {script_type}")
        print(f"Target: {job.get('target_name', 'Unknown')}")
        print(f"Frame type: {job.get('type', 'Unknown')}")
        print(f"Filter: {job.get('filter', 'None')}")
        print(f"Exposure: {job.get('exposure', 0)} seconds")
        print(f"Binning: {job.get('binning_x', 1)}x{job.get('binning_y', 1)}")

        # Handle different script types
        if script_type == "POST_CAPTURE":
            # Access FITS file information
            fits = input_data.get("fits", {})
            filename = fits.get("filename", "")
            print(f"Captured file: {filename}")

            # Access FITS headers
            headers = fits.get("headers", {})
            if headers:
                print("FITS Headers:")
                for key, value in headers.items():
                    print(f"  {key}: {value}")

            # Log progress
            progress = input_data.get("progress", {})
            completed = progress.get("completed", 0)
            total = progress.get("total", 0)
            print(f"Job progress: {completed}/{total} images")

            # Add your custom logic here, e.g.:
            # - Copy file to backup location
            # - Update a database
            # - Send a notification
            # - Trigger external processing

        elif script_type == "POST_JOB":
            # Job completed, log sequence progress
            progress = input_data.get("progress", {})
            completed = progress.get("completed", 0)
            total = progress.get("total", 0)
            print(f"Sequence progress: {completed}/{total} jobs completed")

            # Add your custom logic here, e.g.:
            # - Send completion notification
            # - Update observatory status
            # - Clean up temporary files

        # Exit with success code
        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON input: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
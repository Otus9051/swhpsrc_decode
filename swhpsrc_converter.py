import argparse
import struct
import sys
import os
import glob
import subprocess

def parse_swhpsrc(filepath):
    """
    Parses a Sonarworks .swhpsrc file and extracts the primary frequency response curve.
    Returns a list of (frequency, amplitude) tuples.
    """
    try:
        with open(filepath, "rb") as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

    # Check magic bytes just in case (usually 'PEQb')
    if not data.startswith(b'PEQb'):
        print(f"Warning: {filepath} does not start with expected 'PEQb' magic bytes.")

    # Find the start of Block 0. It usually begins around offset 63 and the first frequency is ~20.0 Hz.
    start = -1
    for offset in range(0, min(1000, len(data)-24)):
        try:
            v1 = struct.unpack("<d", data[offset:offset+8])[0]
            if 19.999 < v1 < 20.001:
                start = offset
                break
        except:
            pass

    if start == -1:
        print(f"Error: Could not find frequency 20.0 in {filepath}. Is it a valid .swhpsrc?")
        return None

    points = []
    # Typically there are ~355 points up to ~22000Hz
    for i in range(1000):
        try:
            v1 = struct.unpack("<d", data[start + i*24 : start + i*24 + 8])[0]
            v2 = struct.unpack("<d", data[start + i*24 + 8 : start + i*24 + 16])[0]
            # Stop if the frequency goes out of typical human hearing bounds or wraps around
            if v1 < 10 or v1 > 25000:
                break
            points.append((v1, v2))
        except:
            break

    if not points:
        print(f"Error: No valid data points found in {filepath}.")
        return None

    return points

def export_to_csv(points, out_filepath):
    """
    Exports the frequency response points to an AutoEQ compatible CSV file.
    """
    try:
        with open(out_filepath, "w") as f:
            f.write("frequency,raw\n")
            for freq, amp in points:
                f.write(f"{freq:.2f},{amp:.2f}\n")
        print(f"Successfully wrote CSV: {out_filepath}")
        return True
    except Exception as e:
        print(f"Error writing to {out_filepath}: {e}")
        return False

def run_autoeq(csv_filepath):
    """
    Attempts to run AutoEQ on the generated CSV file.
    """
    out_dir = os.path.splitext(csv_filepath)[0] + "_AutoEQ"
    print(f"\nAttempting to run AutoEQ on {csv_filepath}...")

    # Check if autoeq is accessible via command line
    cmd = [
        sys.executable, "-m", "autoeq",
        "--input-file", csv_filepath,
        "--output-dir", out_dir
    ]

    try:
        # We don't strictly require AutoEQ to succeed if it's not installed.
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"AutoEQ finished successfully! Results saved to {out_dir}/")
        else:
            print("AutoEQ failed. Make sure AutoEQ is installed (`pip install autoeq`).")
            print("AutoEQ Error output:")
            print(result.stderr)
    except FileNotFoundError:
        print("Could not find Python executable to run AutoEQ. Is it installed?")
    except Exception as e:
        print(f"An unexpected error occurred while running AutoEQ: {e}")

def process_file(filepath):
    print(f"\nProcessing {filepath}...")
    points = parse_swhpsrc(filepath)
    if not points:
        return

    out_csv = os.path.splitext(filepath)[0] + ".csv"
    success = export_to_csv(points, out_csv)

    if success:
        run_autoeq(out_csv)

def main():
    parser = argparse.ArgumentParser(description="Convert Sonarworks .swhpsrc files to AutoEQ CSVs and optionally run AutoEQ.")
    parser.add_argument("files", nargs="*", help="Specific .swhpsrc files to process.")
    parser.add_argument("--all", action="store_true", help="Process all .swhpsrc files in the current directory.")

    args = parser.parse_args()

    files_to_process = []

    if args.all:
        files_to_process.extend(glob.glob("*.swhpsrc"))

    if args.files:
        files_to_process.extend(args.files)

    # Remove duplicates if any
    files_to_process = list(set(files_to_process))

    if not files_to_process:
        print("No files to process. Please provide file paths or use the --all flag.")
        parser.print_help()
        sys.exit(1)

    for f in files_to_process:
        if not os.path.exists(f):
            print(f"File not found: {f}")
            continue
        process_file(f)

if __name__ == "__main__":
    main()

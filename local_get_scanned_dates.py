"""
local_get_scanned_dates.py
---------------------------
Extract scan dates from SVS whole-slide images stored in a local/hipergator directory.

Usage:
    python local_get_scanned_dates.py --svs_dir <SVS_DIRECTORY> --output_path <OUTPUT_DIR>

Example:
    python local_get_scanned_dates.py \
        --svs_dir /orange/pinaki.sarder/Davy_Jones_Locker/Transplant_R01/MayoQC/ \
        --output_path scanned_dates_output
"""

import os
import csv
import argparse
import openslide


def get_scan_date_from_slide(filepath):
    """Open an SVS/whole-slide image and return the scan date, or None."""
    try:
        slide = openslide.OpenSlide(filepath)

        # 1) Direct Aperio property
        date = slide.properties.get("aperio.Date", None)

        # 2) Fallback: parse pipe-delimited ImageDescription
        if not date:
            desc = slide.properties.get("tiff.ImageDescription", "")
            for field in desc.split("|"):
                field = field.strip()
                if field.lower().startswith("date ="):
                    date = field.split("=", 1)[1].strip()
                    break

        slide.close()
        return date

    except Exception as e:
        return f"Error: {e}"


def main():
    parser = argparse.ArgumentParser(
        description="Extract scan dates from SVS files in a local directory."
    )
    parser.add_argument(
        "--svs_dir",
        required=True,
        help="Path to directory containing .svs files",
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Directory where the output CSV will be saved",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.svs_dir):
        raise ValueError(f"SVS directory not found: {args.svs_dir}")

    os.makedirs(args.output_path, exist_ok=True)
    output_csv = os.path.join(args.output_path, "scanned_dates.csv")

    svs_files = [f for f in os.listdir(args.svs_dir) if f.lower().endswith(".svs")]
    print(f"Found {len(svs_files)} SVS files in {args.svs_dir}")

    with open(output_csv, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "Date"])

        for filename in svs_files:
            filepath = os.path.join(args.svs_dir, filename)
            date = get_scan_date_from_slide(filepath)
            print(f"{filename}: {date}")
            writer.writerow([filename, date])

    print(f"\nDone! Results saved to {output_csv}")


if __name__ == "__main__":
    main()

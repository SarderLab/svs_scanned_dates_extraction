"""
athena_get_scanned_dates.py
-----------------------------
Extract scan dates from SVS whole-slide images stored on an Athena/Girder platform.

Usage:
    python athena_get_scanned_dates.py --folder_id <FOLDER_ID> --output_path <OUTPUT_DIR>

Example:
    python athena_get_scanned_dates.py \
        --folder_id 6862f2a2ee65a10c5a4bf11f \
        --output_path scanned_dates_output
"""

import os
import csv
import argparse
import openslide
import girder_client
from tqdm import tqdm
from collections import defaultdict

API_URL = "https://athena.rc.ufl.edu/api/v1"
API_KEY = "uen1EWKH7cgxYOSDSFl94uqpOnJVyvOxPYbfmyVjsYwxi14GaQhAZzjHZPyr5mju"


def get_all_items(gc, folder_id):
    """Fetch every item in a Girder folder, paginating as needed."""
    all_items = []
    limit = 200
    offset = 0
    while True:
        batch = gc.get("/item", parameters={
            "folderId": folder_id,
            "limit":    limit,
            "offset":   offset,
        })
        all_items.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return all_items


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
        description="Extract scan dates from SVS files in an Athena/Girder folder."
    )
    parser.add_argument(
        "--folder_id",
        required=True,
        help="Girder folder ID containing the slide items (e.g. 6862f2a2ee65a10c5a4bf11f)",
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Directory where the output CSV will be saved",
    )
    args = parser.parse_args()

    os.makedirs(args.output_path, exist_ok=True)
    output_csv = os.path.join(args.output_path, "scanned_dates.csv")

    # Connect
    gc = girder_client.GirderClient(apiUrl=API_URL)
    gc.setToken(API_KEY)
    user = gc.get("user/me")
    print(f"Logged in as: {user.get('login', 'unknown')}")

    # Fetch items
    items = get_all_items(gc, args.folder_id)
    print(f"Found {len(items)} items in folder {args.folder_id}")

    # Group by patient ID (first token of item name, e.g. "IU02")
    patient_slides = defaultdict(list)
    for item in items:
        patient_id = item["name"].split()[0]
        patient_slides[patient_id].append(item)

    # Temp dir for downloads
    tmp_dir = os.path.join(args.output_path, "_tmp_slides")
    os.makedirs(tmp_dir, exist_ok=True)

    results = []

    for patient_id, slides in tqdm(patient_slides.items(), desc="Processing patients"):
        slides_sorted = sorted(slides, key=lambda x: x["name"])

        for item in slides_sorted:
            item_id   = item["_id"]
            item_name = item["name"]

            files     = gc.get(f"/item/{item_id}/files")
            svs_files = [f for f in files if f["name"].lower().endswith(".svs")]

            if not svs_files:
                results.append({
                    "patient_id":   patient_id,
                    "item_name":    item_name,
                    "item_id":      item_id,
                    "file_name":    "N/A",
                    "scanned_date": "No SVS file found",
                })
                continue

            for svs_file in svs_files:
                file_id   = svs_file["_id"]
                file_name = svs_file["name"]
                tmp_path  = os.path.join(tmp_dir, file_name)

                try:
                    gc.downloadFile(file_id, tmp_path)
                    scanned_date = get_scan_date_from_slide(tmp_path)
                except Exception as e:
                    scanned_date = f"Download error: {e}"
                finally:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)

                print(f"  {item_name} / {file_name}: {scanned_date}")
                results.append({
                    "patient_id":   patient_id,
                    "item_name":    item_name,
                    "item_id":      item_id,
                    "file_name":    file_name,
                    "scanned_date": scanned_date,
                })

    # Write CSV
    fieldnames = ["patient_id", "item_name", "item_id", "file_name", "scanned_date"]
    with open(output_csv, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    # Clean up empty temp dir
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    print(f"\nDone! {len(results)} records saved to: {output_csv}")


if __name__ == "__main__":
    main()

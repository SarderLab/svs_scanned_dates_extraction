# svs-scanned-dates

Extract scan dates from SVS whole-slide images — works with both a **local/Hipergator directory** and an **Athena/Girder platform** folder.

---

## Scripts

| Script | Source | Input |
|--------|--------|-------|
| `local_get_scanned_dates.py` | Local filesystem | Path to a directory of `.svs` files |
| `athena_get_scanned_dates.py` | Athena (Girder) | Girder folder ID |

Both scripts write results to a CSV in the output directory you specify.

---

## Installation

```bash
pip install openslide-python girder-client tqdm
```

> **Note:** `openslide` also requires the native OpenSlide library.  
> - Linux: `sudo apt install openslide-tools`  
> - macOS: `brew install openslide`  
> - HiPerGator/cluster: `module load openslide`

---

## Usage

### 1. Local directory

```bash
python local_get_scanned_dates.py \
    --svs_dir /path/to/svs/files/ \
    --output_path scanned_dates_output
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--svs_dir` | Path to the directory containing `.svs` files |
| `--output_path` | Directory where `scanned_dates.csv` will be saved |

**Output CSV columns:** `Filename`, `Date`

---

### 2. Athena / Girder platform

```bash
python athena_get_scanned_dates.py \
    --folder_id 6862f2a2ee65a10c5a4bf11f \
    --output_path scanned_dates_output
```

**Arguments:**

| Argument | Description |
|----------|-------------|
| `--folder_id` | Girder folder ID containing the slide items |
| `--output_path` | Directory where `scanned_dates.csv` will be saved |

**Output CSV columns:** `patient_id`, `item_name`, `item_id`, `file_name`, `scanned_date`

> The script streams each SVS file temporarily to extract its metadata, then deletes the local copy immediately.

---

## How scan dates are extracted

Both scripts try two methods in order:

1. **Direct Aperio property** — `aperio.Date` in the slide's OpenSlide properties
2. **ImageDescription fallback** — parses the pipe-delimited `tiff.ImageDescription` field for a `Date = ...` entry

---

## Output structure

```
scanned_dates_output/
└── scanned_dates.csv           # (Athena) or transplant_mayo_svs_dates.csv (local)
```

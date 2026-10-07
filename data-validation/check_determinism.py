import argparse
import hashlib
import sys
from pathlib import Path

import pandas as pd


def sha256_file(path: Path) -> str:
    """Return SHA-256 hash of a file."""
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_csv(path: Path) -> pd.DataFrame:
    """Load CSV for structural/content comparison."""
    return pd.read_csv(path)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check whether multiple pipeline outputs are deterministic."
        )
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="Two or more CSV outputs produced from the same input.",
    )

    args = parser.parse_args()

    if len(args.files) < 2:
        parser.error("Provide at least two output CSV files.")

    paths = [Path(file) for file in args.files]

    for path in paths:
        if not path.exists():
            print(f"ERROR: File not found: {path}")
            sys.exit(1)

    print("\nDeterminism Validation")
    print("=" * 70)

    results = []

    for path in paths:
        df = load_csv(path)
        file_hash = sha256_file(path)

        results.append(
            {
                "path": path,
                "dataframe": df,
                "hash": file_hash,
            }
        )

        print(f"\nFile:   {path.name}")
        print(f"Rows:   {len(df)}")
        print(f"Cols:   {len(df.columns)}")
        print(f"SHA256: {file_hash}")

    reference = results[0]
    reference_df = reference["dataframe"]
    reference_hash = reference["hash"]

    schema_match = True
    row_count_match = True
    content_match = True
    byte_match = True

    for result in results[1:]:
        df = result["dataframe"]

        if list(df.columns) != list(reference_df.columns):
            schema_match = False

        if len(df) != len(reference_df):
            row_count_match = False

        if not df.equals(reference_df):
            content_match = False

        if result["hash"] != reference_hash:
            byte_match = False

    print("\nComparison")
    print("=" * 70)
    print(f"Schema identical:      {'PASS' if schema_match else 'FAIL'}")
    print(f"Row counts identical:  {'PASS' if row_count_match else 'FAIL'}")
    print(f"Cell content identical:{' PASS' if content_match else ' FAIL'}")
    print(f"Byte-for-byte identical:{' PASS' if byte_match else ' FAIL'}")

    deterministic = (
        schema_match
        and row_count_match
        and content_match
        and byte_match
    )

    print("\n" + "=" * 70)

    if deterministic:
        print(
            "PASS: Outputs are deterministic across repeated runs."
        )
        sys.exit(0)

    print(
        "FAIL: Outputs differ across repeated runs."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
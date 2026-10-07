import argparse
import sys

import pandas as pd


LOWERCASE_COLUMNS = {
    "customer_email",
    "country",
    "status",
    "order_status",
}


def load_csv(path):
    return pd.read_csv(path)


def text_columns(df):
    """
    Return columns containing text/string data without relying on
    select_dtypes(include=["object"]), which produces pandas warnings.
    """
    columns = []

    for col in df.columns:
        if (
            pd.api.types.is_object_dtype(df[col])
            or pd.api.types.is_string_dtype(df[col])
        ):
            columns.append(col)

    return columns


def build_expected(input_df, date_format=None):
    """
    Apply the cleaning rules that the baseline Rhombus pipeline is
    intended to perform.

    date_format can be supplied when the source uses a known date
    convention, e.g. "%d/%m/%Y".
    """
    df = input_df.copy()

    # -------------------------------------------------------
    # 1. Remove duplicate orders
    # -------------------------------------------------------
    if "order_id" in df.columns:
        df = df.drop_duplicates(
            subset=["order_id"],
            keep="first",
        )

    # -------------------------------------------------------
    # 2. Remove quantity <= 0 when quantity is genuinely numeric
    # -------------------------------------------------------
    if "quantity" in df.columns:
        numeric_quantity = pd.to_numeric(
            df["quantity"],
            errors="coerce",
        )

        # Only apply this rule if every quantity can be interpreted
        # numerically. Non-numeric quantity input is treated as drift.
        if numeric_quantity.notna().all():
            df = df[numeric_quantity > 0].copy()

    # -------------------------------------------------------
    # 3. Strip leading/trailing whitespace from text columns
    # -------------------------------------------------------
    for col in text_columns(df):
        df[col] = df[col].apply(
            lambda x: x.strip()
            if isinstance(x, str)
            else x
        )

    # -------------------------------------------------------
    # 4. Lowercase configured text columns
    # -------------------------------------------------------
    for col in LOWERCASE_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda x: x.lower()
                if isinstance(x, str)
                else x
            )

    # -------------------------------------------------------
    # 5. Standardise dates
    # -------------------------------------------------------
    if "order_date" in df.columns:
        if date_format:
            parsed = pd.to_datetime(
                df["order_date"],
                format=date_format,
                errors="coerce",
            )
        else:
            parsed = pd.to_datetime(
                df["order_date"],
                errors="coerce",
            )

        df["order_date"] = parsed.dt.strftime("%Y-%m-%d")

    return df.reset_index(drop=True)


def normalized(df):
    """
    Make comparisons robust to row ordering.
    """
    result = df.copy()

    if "order_id" in result.columns:
        result = result.sort_values("order_id")

    return result.reset_index(drop=True)


def check_text_lowercase(df, column):
    if column not in df.columns:
        return None

    values = df[column].dropna().astype(str)

    bad = values[
        values != values.str.lower()
    ]

    return bad.tolist()


def validate(
    input_path,
    output_path,
    reference_path,
    input_date_format=None,
):
    # -------------------------------------------------------
    # Load data
    # -------------------------------------------------------
    source = load_csv(input_path)
    actual = load_csv(output_path)
    reference_source = load_csv(reference_path)

    # Expected output from THIS run's input.
    expected = build_expected(
        source,
        date_format=input_date_format,
    )

    # Canonical baseline used for semantic-drift detection.
    # The canonical baseline is explicitly ISO YYYY-MM-DD.
    reference = build_expected(
        reference_source,
        date_format="%Y-%m-%d",
    )

    expected = normalized(expected)
    actual = normalized(actual)
    reference = normalized(reference)

    failures = []

    print("=" * 65)
    print("RHOMBUS DATA VALIDATION")
    print("=" * 65)

    print(f"Input:     {input_path}")
    print(f"Output:    {output_path}")
    print(f"Reference: {reference_path}")

    if input_date_format:
        print(f"Input date format: {input_date_format}")

    print()

    # =======================================================
    # SCHEMA VALIDATION
    # =======================================================

    expected_cols = list(expected.columns)
    actual_cols = list(actual.columns)

    missing_cols = [
        col
        for col in expected_cols
        if col not in actual_cols
    ]

    extra_cols = [
        col
        for col in actual_cols
        if col not in expected_cols
    ]

    print(
        f"Expected columns ({len(expected_cols)}): "
        f"{expected_cols}"
    )

    print(
        f"Actual columns   ({len(actual_cols)}): "
        f"{actual_cols}"
    )

    if missing_cols:
        failures.append(
            f"Missing output columns: {missing_cols}"
        )

    if extra_cols:
        failures.append(
            f"Unexpected output columns: {extra_cols}"
        )

    # =======================================================
    # ROW COUNT
    # =======================================================

    print()

    print(f"Expected rows: {len(expected)}")
    print(f"Actual rows:   {len(actual)}")

    if len(expected) != len(actual):
        failures.append(
            f"Row count mismatch: expected {len(expected)}, "
            f"got {len(actual)}"
        )

    # =======================================================
    # DUPLICATE VALIDATION
    # =======================================================

    if "order_id" in actual.columns:
        duplicate_count = (
            actual["order_id"]
            .duplicated()
            .sum()
        )

        print(
            f"Duplicate order IDs: "
            f"{duplicate_count}"
        )

        if duplicate_count:
            failures.append(
                f"{duplicate_count} duplicate "
                f"order_id values remain"
            )

    # =======================================================
    # QUANTITY VALIDATION
    # =======================================================

    if "quantity" in source.columns:
        source_numeric = pd.to_numeric(
            source["quantity"],
            errors="coerce",
        )

        if source_numeric.isna().any():
            print(
                "Quantity input type: "
                "NON-NUMERIC DRIFT DETECTED"
            )

        elif "quantity" in actual.columns:
            actual_numeric = pd.to_numeric(
                actual["quantity"],
                errors="coerce",
            )

            invalid = (
                actual_numeric.isna()
                | (actual_numeric <= 0)
            ).sum()

            print(
                f"Invalid output quantities: "
                f"{invalid}"
            )

            if invalid:
                failures.append(
                    f"{invalid} invalid/non-numeric "
                    f"quantities in output"
                )

    # =======================================================
    # LOWERCASE VALIDATION
    # =======================================================

    for col in sorted(LOWERCASE_COLUMNS):
        bad = check_text_lowercase(
            actual,
            col,
        )

        if bad is not None:
            print(
                f"{col} uppercase violations: "
                f"{len(bad)}"
            )

            if bad:
                failures.append(
                    f"{col} contains values that "
                    f"were not lowercased: "
                    f"{bad[:5]}"
                )

    # =======================================================
    # WHITESPACE VALIDATION
    # =======================================================

    whitespace_problems = []

    for col in text_columns(actual):
        for value in (
            actual[col]
            .dropna()
            .astype(str)
        ):
            if value != value.strip():
                whitespace_problems.append(
                    (col, value)
                )

    print(
        f"Whitespace violations: "
        f"{len(whitespace_problems)}"
    )

    if whitespace_problems:
        failures.append(
            "Leading/trailing whitespace remains: "
            f"{whitespace_problems[:5]}"
        )

    # =======================================================
    # CELL-LEVEL EXPECTED VS ACTUAL
    #
    # Compare Rhombus output against what SHOULD have been
    # produced from the current input.
    # =======================================================

    common_cols = [
        col
        for col in expected.columns
        if col in actual.columns
    ]

    if (
        len(expected) == len(actual)
        and common_cols
    ):
        exp = (
            expected[common_cols]
            .astype("string")
            .fillna("<NULL>")
        )

        act = (
            actual[common_cols]
            .astype("string")
            .fillna("<NULL>")
        )

        diff_mask = exp.ne(act)

        differences = []

        rows, cols = (
            diff_mask
            .to_numpy()
            .nonzero()
        )

        for row_idx, col_idx in zip(
            rows,
            cols,
        ):
            differences.append(
                {
                    "row": row_idx,
                    "column": common_cols[col_idx],
                    "expected": exp.iloc[
                        row_idx,
                        col_idx,
                    ],
                    "actual": act.iloc[
                        row_idx,
                        col_idx,
                    ],
                }
            )

        print(
            "Cell differences from intended "
            f"output: {len(differences)}"
        )

        if differences:
            print("\nFirst differences:")

            for diff in differences[:10]:
                print(
                    f"  row={diff['row']} "
                    f"column={diff['column']} "
                    f"expected={diff['expected']!r} "
                    f"actual={diff['actual']!r}"
                )

            failures.append(
                f"{len(differences)} cell values "
                f"differ from intended output"
            )

    # =======================================================
    # SEMANTIC DRIFT VALIDATION
    #
    # Compare semantically important fields against the
    # canonical baseline.
    # =======================================================

    print()
    print("-" * 65)
    print("SEMANTIC DRIFT CHECKS")
    print("-" * 65)

    if (
        "order_id" in actual.columns
        and "order_id" in reference.columns
    ):
        reference_columns = [
            col
            for col in [
                "order_id",
                "unit_price_usd",
                "order_date",
            ]
            if col in reference.columns
        ]

        semantic = actual.merge(
            reference[reference_columns],
            on="order_id",
            how="inner",
            suffixes=(
                "_actual",
                "_reference",
            ),
        )

        # ---------------------------------------------------
        # PRICE SEMANTICS
        # ---------------------------------------------------

        if (
            "unit_price_usd_actual"
            in semantic.columns
            and
            "unit_price_usd_reference"
            in semantic.columns
        ):
            actual_price = pd.to_numeric(
                semantic[
                    "unit_price_usd_actual"
                ],
                errors="coerce",
            )

            reference_price = pd.to_numeric(
                semantic[
                    "unit_price_usd_reference"
                ],
                errors="coerce",
            )

            price_diff = ~actual_price.eq(
                reference_price
            )

            price_difference_count = int(
                price_diff.sum()
            )

            print(
                "Semantic price differences "
                f"from baseline: "
                f"{price_difference_count}"
            )

            if price_diff.any():
                ratios = (
                    actual_price[price_diff]
                    / reference_price[price_diff]
                )

                example_ratios = (
                    ratios
                    .head(5)
                    .round(2)
                    .tolist()
                )

                failures.append(
                    "Semantic price drift detected "
                    f"in {price_difference_count} "
                    "row(s). "
                    "Example actual/reference "
                    f"ratios: {example_ratios}"
                )

        # ---------------------------------------------------
        # DATE SEMANTICS
        # ---------------------------------------------------

        if (
            "order_date_actual"
            in semantic.columns
            and
            "order_date_reference"
            in semantic.columns
        ):
            # Rhombus output and canonical baseline are both
            # expected to be ISO after processing.
            actual_dates = pd.to_datetime(
                semantic[
                    "order_date_actual"
                ],
                format="%Y-%m-%d",
                errors="coerce",
            )

            reference_dates = pd.to_datetime(
                semantic[
                    "order_date_reference"
                ],
                format="%Y-%m-%d",
                errors="coerce",
            )

            date_diff = ~actual_dates.eq(
                reference_dates
            )

            date_difference_count = int(
                date_diff.sum()
            )

            print(
                "Semantic date differences "
                f"from baseline: "
                f"{date_difference_count}"
            )

            if date_diff.any():
                examples = (
                    semantic.loc[
                        date_diff,
                        [
                            "order_id",
                            "order_date_actual",
                            "order_date_reference",
                        ],
                    ]
                    .head(5)
                    .to_dict("records")
                )

                failures.append(
                    "Semantic date drift detected "
                    f"in {date_difference_count} "
                    "row(s). "
                    f"Examples: {examples}"
                )

    # =======================================================
    # FINAL RESULT
    # =======================================================

    print()
    print("=" * 65)

    if failures:
        print("RESULT: FAIL")
        print("=" * 65)

        for failure in failures:
            print(f"✗ {failure}")

        return 1

    print("RESULT: PASS")
    print("=" * 65)

    print("✓ Schema")
    print("✓ Row count")
    print("✓ Cleaning rules")
    print("✓ Output values")
    print("✓ Semantic checks")

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Validate Rhombus GCS output against "
            "the S3 input and canonical baseline."
        )
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Source CSV used for this run",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="CSV exported by Rhombus to GCS",
    )

    parser.add_argument(
        "--reference",
        default="datasets/baseline.csv",
        help=(
            "Canonical baseline CSV used for "
            "semantic drift checks"
        ),
    )

    parser.add_argument(
        "--input-date-format",
        default=None,
        help=(
            "Optional known date format of the source, "
            "for example %%d/%%m/%%Y"
        ),
    )

    args = parser.parse_args()

    sys.exit(
        validate(
            args.input,
            args.output,
            args.reference,
            args.input_date_format,
        )
    )
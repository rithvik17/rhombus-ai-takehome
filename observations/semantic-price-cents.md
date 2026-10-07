# Semantic Drift — Prices Changed from Dollars to Cents

## Change

Changed the meaning of `unit_price_usd` while keeping the same schema and numeric type.

Examples:

- `35.50` → `3550`
- `24.99` → `2499`
- `12.00` → `1200`

The field name remained `unit_price_usd`.

## Expected Behaviour

Because the column remained numeric and the schema was unchanged, I expected the ETL pipeline might continue successfully.

The key question was whether Rhombus would detect that the values no longer represented the same monetary unit.

## Actual Behaviour

The pipeline completed successfully and produced GCS output.

Rhombus raised no warning or error.

Structural cleaning still worked correctly:

- 19 rows
- 8 columns
- no duplicate `order_id`
- no invalid quantities
- lowercase transformations applied
- whitespace cleaning applied

## Data Validation

The structural output matched the drifted source after normal cleaning.

However, reference-based semantic validation detected a difference in all 19 output rows.

The validator reported:

`Semantic price differences from baseline: 19`

and:

`Example actual/reference ratios: [100.0, 100.0, 100.0, 100.0, 100.0]`

The final result was:

`RESULT: FAIL`

## Interpretation

Rhombus successfully processed the data but did not detect that monetary values had changed from dollars to cents.

This demonstrates that successful ETL execution and structurally valid output do not guarantee semantic correctness.

Independent domain-aware validation was required to identify the problem.

## Chatbot Diagnosis / Fix

Not applicable.

Rhombus did not detect an error or warning, so there was no platform-generated issue to pass to the chatbot.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

High

All price values silently changed meaning by a factor of 100 while the pipeline still reported success.

# Schema Drift — Dropped Column

## Change

Removed the `customer_email` column from the source dataset while leaving the rest of the schema and values unchanged.

The drifted file was uploaded to the same S3 object used by the baseline pipeline.

## Expected Behaviour

The baseline cleaning pipeline explicitly referenced `customer_email` for lowercasing.

I expected Rhombus either to:

- stop or warn because an expected column was missing, or
- adapt to the missing column and continue processing the remaining fields.

## Actual Behaviour

The pipeline completed successfully.

The GCS output contained:

- 19 rows
- 7 columns
- no `customer_email` column
- no duplicate `order_id` values
- no invalid quantities
- correctly normalised `country` and `status` values

The missing column was propagated as an additive schema loss rather than causing the pipeline to fail.

## Logs

Rhombus reported a successful execution and applied the normal cleaning transformations, including duplicate removal, quantity filtering, whitespace trimming, text-case conversion and date conversion.

No schema warning was raised for the missing column.

## Chatbot Diagnosis / Fix

Not applicable.

Rhombus did not report an error or warning, so there was no failure to provide to the chatbot.

## Data Validation

The output structure and cleaning behaviour were checked against the drifted source.

The expected seven-column output was produced and the cleaning rules continued to hold.

## Schedule Behaviour

Scheduled execution was not evaluated for this case because of the separately identified scheduler issue. The case was executed manually.

## Severity

Informational / None

Rhombus handled this schema drift cleanly and did not produce incorrect output.

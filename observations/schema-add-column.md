# Schema Drift — Added Column

## Change

Added a new column:

`sales_channel`

with values such as:

- `online`
- `store`
- `marketplace`

All existing baseline columns remained unchanged.

## Expected Behaviour

Because this was additive schema drift, I expected the pipeline either to preserve the new field or ignore it while continuing the existing cleaning transformations.

## Actual Behaviour

The pipeline completed successfully.

The GCS output contained:

- 19 rows
- 9 columns
- all original baseline fields
- the new `sales_channel` field
- no duplicate orders
- no invalid quantities
- expected lowercase and whitespace cleaning

The new column was preserved in the output.

## Logs

Rhombus reported a successful execution and applied the existing cleaning transformations without raising a warning for the additional field.

## Chatbot Diagnosis / Fix

Not applicable.

No error or warning was produced.

## Data Validation

The output matched the intended drifted dataset after the expected cleaning rules were applied.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

Informational / None

The additive schema drift was handled cleanly.

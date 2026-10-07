# Schema Drift — Renamed Column

## Change

Renamed:

`status` → `order_status`

The rest of the source data was left unchanged.

## Expected Behaviour

The baseline pipeline explicitly lowercased the `status` field.

I expected the rename either to break that transformation, produce a warning, or require adaptation.

## Actual Behaviour

After resetting the pipeline to a verified baseline state, the pipeline completed successfully.

The GCS output contained:

- 19 rows
- 8 columns
- `order_status` instead of `status`
- lowercase `order_status`
- lowercase `customer_email`
- lowercase `country`
- no duplicate `order_id` values
- no invalid quantities

## Data Validation

The independent validator reported:

`RESULT: PASS`

with zero differences from the intended output.

## Logs

Rhombus reported a successful run and propagated the renamed field through the pipeline.

## Chatbot Diagnosis / Fix

Not applicable for the official test because no pipeline error occurred.

## Additional Observation

During an earlier exploratory rename test, the effective pipeline configuration appeared to retain references to `order_status` even after the original baseline source was restored.

This showed that restoring the source file alone was not sufficient to guarantee a clean experimental state.

For the official test, the baseline pipeline was explicitly restored and independently validated before the drift was re-run.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

Informational / None

The clean isolated rename test was handled successfully.

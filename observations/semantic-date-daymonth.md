# Semantic Drift — Date Convention Changed

## Change

Changed the `order_date` convention while keeping the same column and overall schema.

The baseline used ISO dates such as:

`2026-09-01`

The drifted dataset used DD/MM/YYYY values such as:

`01/09/2026`

The intended meaning of `01/09/2026` was 1 September 2026.

## Expected Behaviour

Because the column name and structure remained unchanged, I expected the pipeline might continue successfully.

The main question was whether Rhombus would preserve the intended DD/MM/YYYY interpretation or silently interpret ambiguous dates using another convention.

## Actual Behaviour

The pipeline completed successfully and produced GCS output.

Rhombus did not raise any warning about ambiguous date interpretation.

Structural cleaning still appeared correct:

- 19 output rows
- 8 output columns
- no duplicate `order_id`
- no invalid quantities
- lowercase transformations applied correctly
- no remaining whitespace problems

However, 11 dates were interpreted incorrectly.

Examples:

- `01/09/2026` intended as `2026-09-01` became `2026-01-09`
- `02/09/2026` intended as `2026-09-02` became `2026-02-09`
- `03/09/2026` intended as `2026-09-03` became `2026-03-09`
- `10/09/2026` intended as `2026-09-10` became `2026-10-09`
- `11/09/2026` intended as `2026-09-11` became `2026-11-09`

`09/09/2026` was unaffected because both DD/MM/YYYY and MM/DD/YYYY represent 9 September.

Values after the 12th were not silently swapped because they could not be interpreted as valid MM/DD/YYYY dates in the same way.

## Logs

Rhombus reported the execution as successful.

The transformation log showed:

`Convert Column Type: type_map: {"order_date":"DateTime"}`

with 19 rows and 19 cells affected.

No semantic or date-ambiguity warning was surfaced.

## Data Validation

The validator was run with the intended source convention explicitly specified:

`--input-date-format "%d/%m/%Y"`

It reported:

`Cell differences from intended output: 11`

and:

`Semantic date differences from baseline: 11`

Examples included:

`expected='2026-09-01' actual='2026-01-09'`

`expected='2026-09-02' actual='2026-02-09'`

`expected='2026-09-03' actual='2026-03-09'`

The final result was:

`RESULT: FAIL`

## Interpretation

Rhombus successfully converted the field into syntactically valid DateTime values, but did not preserve the intended meaning of ambiguous DD/MM/YYYY dates.

The output therefore looked valid and the pipeline reported success while containing incorrect calendar dates.

Independent reference-based validation was required to detect the issue.

## Chatbot Diagnosis / Fix

Not applicable.

Rhombus did not detect an error or warning.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

High

The pipeline silently emitted incorrect calendar dates in 11 rows while reporting a successful execution.

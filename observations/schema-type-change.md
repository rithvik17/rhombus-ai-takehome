# Schema Drift — Quantity Type Changed

## Change

Changed `quantity` from numeric values such as:

`2`

to string values such as:

`2 units`

The column name remained unchanged.

## Expected Behaviour

Because the baseline pipeline compares `quantity` numerically against zero, I expected Rhombus either to:

- detect and convert the changed type,
- stop with a clear type-related error, or
- warn about the incompatible schema.

## Actual Behaviour

The pipeline stopped at the `valid_quantity_orders` node.

Rhombus reported:

`'<=' not supported between instances of 'str' and 'int'`

The failing node was:

`valid_quantity_orders`

and the reported generated-code hash was:

`code_sha=be121b681ccf`

No valid GCS output was produced.

## Logs

The generated code attempted to execute:

`input_df_1['quantity'] <= 0`

directly against string values.

This caused a visible runtime failure rather than silent corruption.

## Chatbot Diagnosis

The built-in chatbot correctly diagnosed that the `quantity` column was arriving as a string type.

It stated that the transformation had been updated to call:

`pd.to_numeric(output_df['quantity'], errors='coerce')`

before the numeric comparison.

## Did the Chatbot Fix Work?

No.

After the chatbot reported that the problem was fixed and the pipeline was ready to run, the pipeline failed again with the same error:

`'<=' not supported between instances of 'str' and 'int'`

The same code hash was reported:

`be121b681ccf`

A later transformation log showed that the natural-language prompt had been updated to mention `pd.to_numeric`, but the executable code still contained:

`quantity_invalid = input_df_1['quantity'] <= 0`

and contained no numeric coercion.

This explains why the chatbot reported a successful repair while runtime behaviour remained unchanged.

## Interpretation

The failure itself was clearly surfaced, which reduces the risk of silent data corruption.

However, the recovery workflow was misleading because the chatbot confidently claimed that a repair had been applied when the effective executable code remained incompatible with the drifted input.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

High

The pipeline stopped safely, but the built-in repair workflow incorrectly reported success and did not restore execution.

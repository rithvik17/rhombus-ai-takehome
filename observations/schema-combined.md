# Schema Drift — Combined Changes

## Change

Applied all four schema changes simultaneously:

- removed `customer_email`
- renamed `status` to `order_status`
- changed `quantity` from numeric values to strings such as `2 units`
- added `sales_channel`

## Expected Behaviour

Because multiple baseline assumptions changed at once, I expected the pipeline either to stop with a clear error or partially adapt to some of the changes.

## Actual Behaviour

The pipeline failed at:

`valid_quantity_orders`

with:

`'<=' not supported between instances of 'str' and 'int'`

and:

`code_sha=be121b681ccf`

The quantity type change was therefore the first blocking incompatibility encountered.

Because execution stopped at that node, the full downstream interaction between the dropped, renamed and added columns could not be evaluated in this run.

## Chatbot Diagnosis

The chatbot correctly identified the changed `quantity` type.

It reported that it had updated `valid_quantity_orders` to apply:

`pd.to_numeric(output_df['quantity'], errors='coerce')`

before the comparison.

## Did the Chatbot Fix Work?

No.

Rerunning the pipeline produced the same string/integer comparison error.

The same code hash was reported again:

`be121b681ccf`

This reproduced the recovery failure seen in the standalone type-change case.

## Interpretation

The quantity type change dominated the combined scenario and prevented later transformations from completing.

The runtime failure was visible, but the chatbot repair mechanism again claimed success without restoring a runnable pipeline.

## Schedule Behaviour

Scheduled execution was not evaluated because of the separately identified scheduler issue.

## Severity

High

The pipeline safely stopped, but automated recovery was unsuccessful and incorrectly reported as fixed.

# Scheduler — Active Schedule Did Not Trigger

## Scenario

A working S3 → Rhombus → GCS pipeline was configured with scheduled execution.

Manual execution of the same pipeline succeeded and produced output in GCS.

Both custom cron schedules and a preset schedule were tested.

Examples included:

`*/5 * * * *`

and:

`*/15 * * * *`

## Expected Behaviour

Once the schedule was active, the pipeline should execute at the configured time and produce:

- an execution record
- a success or failure state
- a corresponding GCS output if successful

## Actual Behaviour

The schedule initially displayed as active and showed an upcoming run.

When the scheduled time arrived:

- no execution occurred
- no entry appeared in Schedule History
- no failure was recorded
- no GCS output was created
- the displayed next-run value became blank

Manual execution of the same pipeline continued to work.

The behaviour occurred with both custom and preset scheduling options.

## Support Response

The issue was reported to the Rhombus AI team.

The response was:

> You should report this as a bug.

This confirmed that the behaviour should be treated as a platform issue rather than an intended scheduling configuration.

## Impact on Testing

Because scheduled executions did not trigger, the required drift scenarios were executed manually.

The scheduling limitation is documented transparently throughout the observations rather than representing the manual runs as scheduled runs.

## Severity

High

Scheduled execution is a core part of an ETL workflow. An active schedule that silently does not execute, while also creating no failure record, can result in stale downstream data without an obvious operational signal.

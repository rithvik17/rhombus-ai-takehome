# Rhombus AI Take Home

This repository contains my take home exercise for the Software Engineer Intern, LLM Observability and Quality Assurance role.

The exercise focuses on testing a Rhombus ETL workflow that reads a CSV from AWS S3, applies a cleaning pipeline built through AI Builder, and writes the cleaned result to Google Cloud Storage.

I tested the workflow from a few different angles: UI automation, direct backend/API testing, data validation, schema drift, semantic drift, determinism, scheduling and general usability.

## Baseline pipeline

The baseline input is `datasets/baseline.csv`.

The cleaning pipeline does the following:

1. Removes duplicate rows using `order_id`, keeping the first occurrence.
2. Removes rows where `quantity <= 0`.
3. Trims leading and trailing whitespace from text fields.
4. Converts `customer_email`, `country` and `status` to lowercase.
5. Standardises `order_date`.
6. Writes the cleaned output as CSV to Google Cloud Storage.

The baseline input has 21 rows. The expected cleaned output has 19 rows and 8 columns.

One duplicate row and one invalid quantity row are removed.

## Repository structure

```text
.
├── api-tests/
│   └── test_background_jobs.py
├── data-validation/
│   ├── validate.py
│   └── check_determinism.py
├── datasets/
│   ├── baseline.csv
│   ├── schema-drop-column.csv
│   ├── schema-rename-column.csv
│   ├── schema-type-change.csv
│   ├── schema-add-column.csv
│   ├── schema-combined.csv
│   ├── semantic-price-cents.csv
│   ├── semantic-date-format.csv
│   └── semantic-date-daymonth.csv
├── observations/
│   ├── evidence/
│   ├── schema-drop-column.md
│   ├── schema-rename-column.md
│   ├── schema-type-change.md
│   ├── schema-add-column.md
│   ├── schema-combined.md
│   ├── semantic-price-cents.md
│   ├── semantic-date-daymonth.md
│   ├── scheduler-not-triggering.md
│   └── pipeline-persistence-after-login.md
├── ui-tests/
│   ├── test_project_navigation.py
│   ├── test_pipeline_run.py
│   ├── test_pipeline_structure.py
│   └── test_schedule.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Setup

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

Copy the environment file:

```bash
cp .env.example .env
```

Populate the following values locally:

```env
RHOMBUS_API_BASE_URL=https://api.rhombusai.com
RHOMBUS_ORG_ID=
RHOMBUS_JOB_ID=
RHOMBUS_ACCESS_TOKEN=
```

Secrets, cloud credentials and local authentication state are excluded from Git.

## Playwright authentication

The UI tests use a local Playwright storage state.

Create it with:

```bash
playwright codegen \
  --save-storage=playwright/.auth/rhombus.json \
  https://rhombusai.com
```

Log in normally and close the browser once authentication is complete.

The storage state file is ignored by Git.

## UI tests

Run:

```bash
pytest ui-tests -v
```

The UI suite currently covers:

1. Opening the take home project from the dashboard.
2. Verifying the configured S3 input and `baseline.csv`.
3. Verifying the AI Builder pipeline structure and cleaning steps.
4. Verifying the configured GCS output destination and CSV export.
5. Starting a real pipeline run and asserting the backend response.
6. Creating a schedule and checking that it becomes active.

Latest full run:

```text
4 passed
```

The tests use Playwright assertions and response/event waits rather than fixed sleeps.

## API tests

The backend endpoint used in the API tests was identified from browser network activity.

Run:

```bash
pytest api-tests -v
```

The positive test makes an authenticated request to the background job endpoint and checks the response status and content.

The negative test calls the same job endpoint without the bearer token.

Observed unauthenticated response:

```text
HTTP 404
{"detail":"No Job matches the given query."}
```

Latest run:

```text
2 passed
```

## Data validation

`data-validation/validate.py` compares a Rhombus output with the corresponding input and the canonical baseline.

It checks:

1. Schema.
2. Row count.
3. Duplicate removal.
4. Quantity filtering.
5. Lowercase conversion.
6. Leading and trailing whitespace.
7. Cell level expected output.
8. Price semantics against the canonical baseline.
9. Date semantics against the canonical baseline.

Example:

```bash
python data-validation/validate.py \
  --input datasets/baseline.csv \
  --output path/to/cleaned_output.csv
```

For the DD/MM/YYYY date drift case:

```bash
python data-validation/validate.py \
  --input datasets/semantic-date-daymonth.csv \
  --output path/to/output.csv \
  --input-date-format "%d/%m/%Y"
```

## Determinism

I also ran the same baseline pipeline twice and compared both outputs using:

```bash
python data-validation/check_determinism.py \
  output_run_1.csv \
  output_run_2.csv
```

The two outputs had the same schema, row count, cell content and SHA256 hash.

```text
Schema identical:       PASS
Row counts identical:   PASS
Cell content identical: PASS
Byte-for-byte identical: PASS
```

Both files had this SHA256 value:

```text
3870e4d6fbc4c347e8127e94048c6eed1789df9f129eb62d13d8c9e7a90b7b79
```

Evidence is saved in `observations/evidence/baseline-determinism.txt`.

## Drift experiments

| Experiment | Pipeline result | What happened | Severity |
| --- | --- | --- | --- |
| Drop `customer_email` | Success | Remaining schema and cleaning behaviour were preserved | Informational |
| Rename `status` to `order_status` | Success | Renamed column was preserved and cleaned correctly | Informational |
| Change `quantity` to strings | Failure | Pipeline failed on a string/int comparison | High |
| Add `sales_channel` | Success | New column was preserved correctly | Informational |
| Combined schema drift | Failure | Quantity type drift blocked the run before later changes could be evaluated | High |
| Price dollars to cents | Success | Pipeline completed but all 19 prices were semantically wrong by a factor of 100 | High |
| ISO date to DD/MM/YYYY | Success | Pipeline completed but 11 dates were interpreted incorrectly | High |

Each experiment has a separate Markdown write up under `observations/`.

## Main findings

### 1. Semantic drift can pass through a successful pipeline

The most important issue I found was that structurally valid data could still be wrong in meaning.

For the price drift test, I multiplied `unit_price_usd` values by 100 while keeping the same column name, numeric type and schema.

Rhombus completed successfully and did not raise a warning.

Structural checks still passed, but comparison against the canonical baseline showed that all 19 matched prices had changed by exactly a factor of 100.

The DD/MM/YYYY date test showed a similar problem. Rhombus completed successfully, but 11 dates were interpreted incorrectly because ambiguous values were parsed month first.

Evidence:

`observations/evidence/semantic-price-cents.txt`

`observations/evidence/semantic-date-daymonth.txt`

### 2. AI Builder said a repair was fixed even though the executable code had not changed

Changing `quantity` from numeric values to strings caused this error:

```text
'<=' not supported between instances of 'str' and 'int'
```

AI Builder correctly diagnosed the problem and said that it had updated the transformation to use `pd.to_numeric(..., errors='coerce')`.

However, rerunning the pipeline produced the same error.

Backend inspection showed that the natural language description had changed, but the effective executable code still contained:

```python
quantity_invalid = input_df_1['quantity'] <= 0
```

The executable code hash also remained:

```text
be121b681ccf
```

This was one of the more interesting observability issues because the conversational state and the code that actually ran were not in sync.

Evidence:

`observations/evidence/schema-type-change-chatbot.png`

`observations/evidence/schema-type-change-rerun.txt`

`observations/evidence/schema-type-change.txt`

### 3. Scheduling could be configured but did not actually trigger a run

I could create schedules successfully and the UI showed them as Active with a next run time.

At the scheduled time, no execution appeared in Schedule History and no new output appeared in GCS.

Manual execution of the same pipeline still worked.

I reproduced this with more than one schedule configuration. Rhombus support replied that this should be reported as a bug.

Because of this, I did not represent a scheduled baseline run as successful. The drift experiments were run manually after confirming that the scheduling UI itself could be configured and automated.

Evidence:

`observations/scheduler-not-triggering.md`

`observations/evidence/scheduler-not-triggering.txt`

## Additional usability observation

I also saw an issue after logging out and signing in again.

The project and AI Builder conversation history were still present, but the pipeline canvas appeared empty. At the same time, AI Builder said that the baseline pipeline was already correctly configured and that the nodes were intact.

I rebuilt the baseline pipeline through AI Builder before continuing the experiments.

This looked like another case where the conversation state, visible canvas state and actual executable state were not fully aligned.

Evidence:

`observations/pipeline-persistence-after-login.md`

`observations/evidence/pipeline-persistence-after-login.png`

## Experiment process

To avoid one drift test affecting another, I used the same reset process for the official runs:

```text
restore baseline source
restore baseline pipeline
run and validate baseline
apply one drift
run and record behaviour
restore baseline before the next experiment
```

This mattered because an earlier exploratory rename test showed that transformation state could persist and affect later runs.

## What I liked

AI Builder made it easy to describe a cleaning workflow quickly in natural language.

The visual pipeline was also useful for understanding the transformation order, and the backend job response gave enough structured information to test execution directly.

Having both a UI view and inspectable backend state made it possible to compare what the product said had happened with what actually ran.

## Things I would improve

A few areas stood out during testing.

1. A schedule should not continue to look healthy if it never triggers and there is no execution record.
2. AI Builder should only confirm that a repair is fixed once the executable transformation has actually changed.
3. Semantic drift checks would be useful alongside schema checks because valid types do not always mean valid values.
4. The canvas and AI Builder history should stay consistent across login sessions.
5. Failed runs would be easier to debug if the UI exposed the exact transformation version or code revision that was executed.

## Evidence

Supporting files are stored in `observations/evidence/`.

Current evidence includes:

```text
baseline-determinism.txt
baseline-restored-output.csv
pipeline-persistence-after-login.png
scheduler-not-triggering.txt
schema-type-change-chatbot.png
schema-type-change-rerun.txt
schema-type-change.txt
semantic-date-daymonth.txt
semantic-price-cents.txt
```

## Demo video

Demo video:

https://drive.google.com/file/d/15LPBGD1sQzx4Ou8nZKz3MDBkHfBabsR5/view?usp=sharing

The video will show the baseline pipeline, the automated UI and API tests, baseline/determinism validation and the main drift findings.

## Useful commands

Run all UI tests:

```bash
pytest ui-tests -v
```

Run API tests:

```bash
pytest api-tests -v
```

Run baseline validation:

```bash
python data-validation/validate.py \
  --input datasets/baseline.csv \
  --output path/to/baseline_output.csv
```

Run determinism validation:

```bash
python data-validation/check_determinism.py \
  output_run_1.csv \
  output_run_2.csv
```

## AI use declaration

I used ChatGPT while working on this exercise to help me debug parts of the Playwright, API and validation code, think through some test cases, and improve the wording and structure of parts of the documentation.

I reviewed and adapted the code myself, ran all of the tests and experiments, and checked the outputs before including them in this repository. The observations and results reported here come from my own runs of the Rhombus platform.

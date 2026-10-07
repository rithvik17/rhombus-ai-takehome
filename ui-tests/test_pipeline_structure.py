import re

from playwright.sync_api import (
    sync_playwright,
    expect,
    TimeoutError as PlaywrightTimeoutError,
)


PROJECT_NAME = "Rhombus Take-Home ETL"


def dismiss_ad_blocker_if_present(page):
    """
    Dismiss Rhombus's intermittent ad-blocker modal when present.
    """
    dialog = page.get_by_role(
        "dialog",
        name="Ad Blocker Detected",
    )

    try:
        dialog.wait_for(
            state="visible",
            timeout=3000,
        )
    except PlaywrightTimeoutError:
        return

    continue_button = dialog.get_by_role(
        "button",
        name="Continue Anyway",
    )

    expect(continue_button).to_be_visible()
    continue_button.click()

    expect(dialog).to_be_hidden(
        timeout=5000,
    )


def test_pipeline_source_transformations_and_destination():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
        )

        context = browser.new_context(
            storage_state="playwright/.auth/rhombus.json",
        )

        page = context.new_page()

        # ---------------------------------------------------
        # Open the real project
        # ---------------------------------------------------
        page.goto(
            "https://rhombusai.com",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        dismiss_ad_blocker_if_present(page)

        project_card = page.get_by_test_id(
            "project-card",
        ).filter(
            has_text=PROJECT_NAME,
        )

        expect(project_card).to_be_visible(
            timeout=20000,
        )

        project_card.click()

        expect(page).to_have_url(
            re.compile(r".*/workflow/5287"),
            timeout=20000,
        )

        dismiss_ad_blocker_if_present(page)

        # ---------------------------------------------------
        # Verify AI Builder produced the baseline pipeline
        # ---------------------------------------------------
        ai_builder = page.get_by_role(
            "tab",
            name="AI Builder",
        )

        expect(ai_builder).to_be_visible(
            timeout=10000,
        )

        ai_builder.click()

        expect(
            page.get_by_text(
                "The baseline pipeline has been fully rebuilt on the canvas.",
                exact=False,
            )
        ).to_be_visible(
            timeout=10000,
        )

        # ---------------------------------------------------
        # S3 input
        # ---------------------------------------------------
        expect(
            page.get_by_text(
                "Loads baseline.csv from the S3 source.",
                exact=False,
            )
        ).to_be_visible()

        # ---------------------------------------------------
        # Cleaning transformations
        # ---------------------------------------------------
        expect(
            page.get_by_text(
                re.compile(
                    r"Removes duplicate rows based on.*order_id",
                    re.IGNORECASE,
                )
            )
        ).to_be_visible()

        expect(
            page.get_by_text(
                re.compile(
                    r"Filters out rows where.*quantity",
                    re.IGNORECASE,
                )
            )
        ).to_be_visible()

        expect(
            page.get_by_text(
                re.compile(
                    r"Trims leading/trailing whitespace",
                    re.IGNORECASE,
                )
            )
        ).to_be_visible()

        expect(
            page.get_by_text(
                re.compile(
                    r"Converts.*customer_email.*country.*status.*lowercase",
                    re.IGNORECASE,
                )
            )
        ).to_be_visible()

        expect(
            page.get_by_text(
                re.compile(
                    r"Standardises.*order_date",
                    re.IGNORECASE,
                )
            )
        ).to_be_visible()

        # ---------------------------------------------------
        # GCS output
        # ---------------------------------------------------
        expect(
            page.get_by_text(
                "Exports the cleaned dataset as a CSV to the GCS destination.",
                exact=False,
            )
        ).to_be_visible()

        # ---------------------------------------------------
        # Open real S3 input configuration
        # ---------------------------------------------------
        baseline_button = page.get_by_role(
            "button",
            name=re.compile(r"baseline_input"),
        ).first

        expect(baseline_button).to_be_visible()
        baseline_button.click()

        dismiss_ad_blocker_if_present(page)

        right_sidebar = page.get_by_test_id(
            "right-sidebar",
        )

        expect(right_sidebar).to_be_visible(
            timeout=10000,
        )

        expect(
            right_sidebar.get_by_text(
                "Data Input",
                exact=True,
            )
        ).to_be_visible()

        # Check the actual S3 source file list
        source_list = right_sidebar.get_by_role(
            "list"
        )

        expect(
            source_list.get_by_text(
                "baseline.csv",
                exact=True,
            )
        ).to_be_visible()

        # ---------------------------------------------------
        # Return to AI Builder and open GCS output config
        # ---------------------------------------------------
        ai_builder = page.get_by_role(
            "tab",
            name="AI Builder",
        )

        expect(ai_builder).to_be_visible()
        ai_builder.click()

        output_button = page.get_by_role(
            "button",
            name=re.compile(r"cleaned_orders_output"),
        ).first

        expect(output_button).to_be_visible(
            timeout=10000,
        )

        output_button.click()

        dismiss_ad_blocker_if_present(page)

        # ---------------------------------------------------
        # Verify actual GCS destination configuration
        # ---------------------------------------------------
        right_sidebar = page.get_by_test_id(
            "right-sidebar",
        )

        expect(right_sidebar).to_be_visible(
            timeout=10000,
        )

        expect(
            right_sidebar.get_by_text(
                "Data Output",
                exact=True,
            )
        ).to_be_visible()

        expect(
            right_sidebar.get_by_text(
                "rithvik-rhombus-takehome-output",
                exact=True,
            )
        ).to_be_visible()

        # Verify CSV is the selected export format.
        # We assert the actual select value rather than the
        # duplicated visible "CSV" text.
        export_format = right_sidebar.locator(
            'select:has(option[value="csv"])'
        )

        expect(export_format).to_have_value(
            "csv"
        )

        # Verify the configured output filename
        filename_input = right_sidebar.locator(
            'input[value="cleaned_orders_export"]'
        )

        expect(filename_input).to_be_visible()

        browser.close()
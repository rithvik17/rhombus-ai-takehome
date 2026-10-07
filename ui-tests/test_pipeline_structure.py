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

        ad_blocker_dialog = page.get_by_role(
            "dialog",
            name="Ad Blocker Detected",
        )

        page.add_locator_handler(
            ad_blocker_dialog,
            lambda: ad_blocker_dialog.get_by_role(
                "button",
                name="Continue Anyway",
            ).click(),
        )

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
        # Verify AI Builder pipeline structure
        # ---------------------------------------------------
        ai_builder = page.get_by_role(
            "tab",
            name="AI Builder",
        )

        expect(ai_builder).to_be_visible(
            timeout=10000,
        )

        ai_builder.click()

        # AI Builder wording can change between rebuilds,
        # so assert the generated node names instead.
        expected_nodes = [
            "baseline_input",
            "deduped_orders",
            "valid_quantity_orders",
            "trimmed_orders",
            "lowercased_orders",
            "cleaned_orders",
            "cleaned_orders_output",
        ]

        for node_name in expected_nodes:
            node_button = page.get_by_role(
                "button",
                name=re.compile(node_name),
            ).first

            expect(node_button).to_be_visible(
                timeout=10000,
            )

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
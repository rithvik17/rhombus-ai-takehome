import re

from playwright.sync_api import (
    sync_playwright,
    expect,
    TimeoutError as PlaywrightTimeoutError,
)


PROJECT_NAME = "Rhombus Take-Home ETL"


def dismiss_ad_blocker(page):
    """
    Dismiss Rhombus's intermittent ad-blocker modal if it appears.
    """
    dialog = page.get_by_role(
        "dialog",
        name="Ad Blocker Detected",
    )

    try:
        dialog.wait_for(
            state="visible",
            timeout=5000,
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


def test_create_schedule():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
        )

        context = browser.new_context(
            storage_state="playwright/.auth/rhombus.json",
        )

        page = context.new_page()

        # Open dashboard.
        page.goto(
            "https://rhombusai.com",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        dismiss_ad_blocker(page)

        # Open the take-home project.
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

        dismiss_ad_blocker(page)

        # Open Schedule.
        schedule_tab = page.get_by_role(
            "tab",
            name="Schedule",
        )

        expect(schedule_tab).to_be_visible(
            timeout=20000,
        )

        schedule_tab.click()

        # The blocker often appears shortly AFTER opening Schedule,
        # so handle it again here.
        dismiss_ad_blocker(page)

        # ---------------------------------------------------
        # Open schedule creation form
        # ---------------------------------------------------
        create_first = page.get_by_role(
            "button",
            name="Create your first schedule",
        )

        add_schedule = page.get_by_role(
            "button",
            name="Add Schedule",
        )

        try:
            create_first.wait_for(
                state="visible",
                timeout=5000,
            )
            create_first.click()
        except PlaywrightTimeoutError:
            # The blocker can occasionally appear between checks.
            dismiss_ad_blocker(page)

            expect(add_schedule).to_be_visible(
                timeout=10000,
            )
            add_schedule.click()

        dismiss_ad_blocker(page)

        # ---------------------------------------------------
        # Configure schedule
        # ---------------------------------------------------
        frequency = page.get_by_role(
            "combobox",
        )

        expect(frequency).to_be_visible(
            timeout=10000,
        )

        expect(frequency).to_have_text(
            "Daily",
        )

        time_input = page.get_by_role(
            "textbox",
            name="Time",
        )

        expect(time_input).to_be_visible()
        time_input.fill("23:59")

        create_button = page.get_by_role(
            "button",
            name="Create",
            exact=True,
        )

        expect(create_button).to_be_visible()
        expect(create_button).to_be_enabled()

        # Keyboard submission avoids a Rhombus backdrop that can
        # intercept pointer clicks in headless Chromium.
        create_button.focus()
        create_button.press("Enter")

        dismiss_ad_blocker(page)

        # ---------------------------------------------------
        # Verify real scheduling outcome
        # ---------------------------------------------------
        schedule_panel = page.get_by_role(
            "complementary",
        )

        expect(schedule_panel).to_be_visible(
            timeout=15000,
        )

        expect(schedule_panel).to_contain_text(
            "Active",
        )

        expect(schedule_panel).to_contain_text(
            "daily",
        )

        expect(schedule_panel).to_contain_text(
            "At 11:59pm",
        )

        active_switch = page.get_by_role(
            "switch",
            name="Deactivate schedule",
        ).first

        expect(active_switch).to_be_visible()
        expect(active_switch).to_be_checked()

        browser.close()
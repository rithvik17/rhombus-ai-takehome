from playwright.sync_api import sync_playwright, expect


def test_open_takehome_project():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            storage_state="playwright/.auth/rhombus.json"
        )

        page = context.new_page()

        page.goto(
            "https://rhombusai.com",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        project_card = page.get_by_test_id("project-card").filter(
            has_text="Rhombus Take-Home ETL"
        )

        expect(project_card).to_be_visible(
            timeout=20000
        )

        project_card.click()

        expect(page).to_have_url(
            "https://rhombusai.com/workflow/5287",
            timeout=20000,
        )

        browser.close()
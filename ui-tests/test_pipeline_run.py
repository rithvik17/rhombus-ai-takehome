from playwright.sync_api import sync_playwright, expect


def test_run_pipeline_from_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        context = browser.new_context(
            storage_state="playwright/.auth/rhombus.json"
        )

        page = context.new_page()

        page.goto(
            "https://rhombusai.com/workflow/5287",
            wait_until="domcontentloaded",
            timeout=30000,
        )

        run_button = page.get_by_test_id("run-pipeline")

        expect(run_button).to_be_visible(
            timeout=20000
        )

        with page.expect_response(
            lambda response:
                "/pipeline/process" in response.url
                and response.request.method == "POST",
            timeout=30000,
        ) as response_info:
            run_button.click()

        response = response_info.value

        assert response.status == 200

        data = response.json()

        assert data["message"] == "Pipeline execution started."
        assert data["task_id"]
        assert data["execution_mode"] == "auto"

        browser.close()
from playwright.sync_api import sync_playwright

URL = "https://www.adcountymedia.com/products/genwin"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_default_timeout(60000)

    print(f"Navigating to {URL}...")
    page.goto(URL, wait_until="domcontentloaded", timeout=60000)

    for _ in range(5):
        page.evaluate("window.scrollBy(0, 2000)")
        page.wait_for_timeout(1000)
    page.wait_for_timeout(2000)

    # Click Full Customer Acquisition and dump surrounding DOM
    btn = page.locator("button:has-text('Full Customer Acquisition')").first
    btn.scroll_into_view_if_needed()
    btn.click(force=True)
    page.wait_for_timeout(2000)

    # Extract ALL text from the page including hidden elements
    all_text = page.evaluate("""() => {
        // Get text including hidden elements
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            null
        );
        let text = '';
        let node;
        while (node = walker.nextNode()) {
            const t = node.textContent.trim();
            if (t.length > 20) {
                text += t + '\\n';
            }
        }
        return text;
    }""")

    print(f"\nALL DOM TEXT ({len(all_text)} chars):")
    # Search for Expert Solutions content specifically
    lines = all_text.split('\n')
    for i, line in enumerate(lines):
        if any(kw in line.lower() for kw in ['customer', 'acquisition', 'pay per', 'call', 'pipeline', 'qualified']):
            # Print surrounding context
            start = max(0, i-2)
            end = min(len(lines), i+5)
            print(f"\n  [line {i}]")
            for l in lines[start:end]:
                print(f"    {l}")

    input("\nPress Enter to close...")
    browser.close()
import asyncio
from playwright.async_api import async_playwright
import os
import sys

async def convert_html_to_pdf(html_filename):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Load the HTML file
        html_path = os.path.abspath(html_filename)
        await page.goto(f'file:///{html_path}')

        # Wait for MathJax to finish rendering
        await page.wait_for_timeout(3000)  # Wait 3 seconds for MathJax

        # Generate PDF with same base name
        pdf_filename = html_filename.replace('.html', '.pdf')
        await page.pdf(
            path=pdf_filename,
            format='A4',
            margin={
                'top': '1in',
                'right': '1in',
                'bottom': '1in',
                'left': '1in'
            },
            print_background=True
        )

        await browser.close()
        print(f"PDF generated successfully: {pdf_filename}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = 'math.html'
    asyncio.run(convert_html_to_pdf(html_file))

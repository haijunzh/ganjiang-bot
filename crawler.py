import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urljoin, urlparse

class GanjiangSpider:
    def __init__(self, start_url):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.visited = set()
        self.knowledge_base = []

    async def scrape(self, page, url):
        if url in self.visited:
            return
        
        print(f"正在抓取 (动态加载): {url}")
        self.visited.add(url)

        try:
            # 访问页面，设置较长的超时并等待网络空闲
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # 1. 提取所有文字内容
            # 过滤掉导航栏、页脚等干扰信息（如果需要更精准，可以指定 selector）
            content = await page.inner_text("body")
            self.knowledge_base.append(f"SOURCE: {url}\n{content}")

            # 2. 提取所有链接
            hrefs = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
            
            internal_links = set()
            for href in hrefs:
                full_url = urljoin(url, href).split('#')[0].rstrip('/')
                if self.domain in full_url and full_url not in self.visited:
                    internal_links.add(full_url)

            # 3. 递归抓取新发现的链接
            for link in internal_links:
                await self.scrape(page, link)

        except Exception as e:
            print(f"抓取 {url} 失败: {e}")

    def save_to_file(self, filename="ganjiang_knowledge.txt"):
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n\n" + "="*50 + "\n\n".join(self.knowledge_base))
        print(f"\n全部抓取完成！共抓取 {len(self.visited)} 个页面。")

async def main():
    spider = GanjiangSpider("https://www.ganjiangyou.cn")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # 改为 False 可以看到浏览器操作过程
        page = await browser.new_page()
        await spider.scrape(page, spider.start_url)
        await browser.close()
    spider.save_to_file()

if __name__ == "__main__":
    asyncio.run(main())
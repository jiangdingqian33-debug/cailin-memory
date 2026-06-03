"""
衍教浏览器Agent v1.0 — 让彩鳞自主浏览网页
"""
import subprocess, json, sys
from playwright.sync_api import sync_playwright

def browse_and_extract(url: str, selector: str = "body") -> str:
    """打开网页并提取指定内容"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # 提取页面文本
            text = page.inner_text(selector)
            title = page.title()
            
            browser.close()
            
            # 截断过长内容
            if len(text) > 3000:
                text = text[:3000] + "\n... (内容已截断)"
            
            return f"📄 {title}\n\n{text}"
    except Exception as e:
        return f"浏览失败：{e}"

def search_and_summarize(query: str) -> str:
    """搜索并总结网页内容"""
    url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_selector('[data-testid="result-title-a"]', timeout=10000)
            
            # 提取前5条搜索结果
            results = page.evaluate('''
                () => {
                    const items = [];
                    const results = document.querySelectorAll('article[data-testid="result"]');
                    results.forEach((r, i) => {
                        if (i >= 5) return;
                        const title = r.querySelector('h2')?.innerText || '';
                        const link = r.querySelector('a[data-testid="result-title-a"]')?.href || '';
                        const snippet = r.querySelector('[data-testid="result-snippet"]')?.innerText || '';
                        items.push({title, link, snippet});
                    });
                    return items;
                }
            ''')
            
            browser.close()
            
            if not results:
                return "未找到搜索结果。"
            
            summary = f"🔍 搜索「{query}」结果：\n\n"
            for i, r in enumerate(results):
                summary += f"{i+1}. **{r['title']}**\n   {r['snippet'][:120]}\n   {r['link']}\n\n"
            
            return summary
    except Exception as e:
        return f"搜索失败：{e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python browser_agent.py <URL或搜索关键词>")
    else:
        query = " ".join(sys.argv[1:])
        if query.startswith("http"):
            print(browse_and_extract(query))
        else:
            print(search_and_summarize(query))

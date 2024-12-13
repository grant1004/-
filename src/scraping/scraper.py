import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from datetime import datetime
import xml.etree.ElementTree as ET
import re
from tqdm import tqdm
import datetime

# 函數 parse_sitemap 用於解析 sitemap 並取出在特定日期範圍內的 sitemap URL。
# 這個函數有三個輸入: url，start_date，和 end_date。
# 函數首先試著從提供的 url 取得內容，並檢測返回的狀態碼。如果狀態碼不是200的話，函數會返回一個空的列表。
# 如果狀態碼確認為200，函數會解析內容為 XML 格式，然後從中提取 sitemap 標籤的 loc 文本。每一個成功提取的 loc 文本都會被加入到 urls 列表中。
# 接下來，函數將按照輸入的日期範圍產生出對應的 url 匹配模式，並用這個模式從 urls 列表中過濾出相對應的 url。
# 最後，函數會回傳這些匹配的 url。
def parse_sitemap(url, start_date, end_date):
    print(f"正在獲取 sitemap: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"獲取 sitemap 失敗。狀態碼：{response.status_code}")
        return []

    print("成功獲取 sitemap")
    print(f"Response content type: {response.headers.get('Content-Type')}")
    print("Response content (first 200 characters):")
    print(response.text[:200])

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"解析 XML 時出錯：{e}")
        return []

    namespaces = {
        'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    }

    urls = []
    for sitemap in root.findall('sm:sitemap', namespaces):
        loc = sitemap.find('sm:loc', namespaces)
        if loc is not None:
            urls.append(loc.text)

    if not urls:
        print("No sub-sitemaps found, trying to parse as a regular sitemap")
        for url in root.findall('sm:url', namespaces):
            loc = url.find('sm:loc', namespaces)
            if loc is not None:
                urls.append(loc.text)

    # 使用正则表达式匹配当前月份的sitemap URL
    date_range = pd.date_range(start=start_date, end=end_date, freq='ME')
    print( date_range )
    # 构建正则表达式模式列表，用于匹配特定日期范围内的sitemap URL
    patterns = [ re.compile(rf'https://technews.tw/sitemap-pt-post-{date.year}-{date.month:02d}\.xml') for date in date_range ]

    # 根据模式匹配sitemap URL
    matched_sitemap_urls = [ url for url in urls for pattern in patterns if pattern.match(url) ]


    print(f"找到 {len(urls)} 個 URL")
    print(f"回傳 target Date 的 URL {matched_sitemap_urls}")
    return matched_sitemap_urls


# `scrape_article` 函數用於從給定的網址中抓取文章的信息。
# 它從給定的網址獲取 HTML 內容，使用 BeautifulSoup 解析它，並提取有關文章的關鍵信息，如 `title`（標題），`date`（日期），`author`（作者）和`content`（內容）。
# 若無法找到任何信息，則此函數會將預設值，如 "標題未找到", "日期未找到", "作者未找到", "內容未找到" 分別添加到相關的字段中。
# 此函數最後會將收集到的字段以字典形式回傳。
#
# 參數:
# `url`: 需要抓取文章的網址連結
#
# 回傳:
# `dictionary`: 包含了在網址中找到的文章的 `title`（標題），`Date`（日期），`Author`（作者）和`Content`（內容）的字典。
def scrape_article(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    title = soup.find('h1', class_='entry-title').text.strip() if soup.find('h1', class_='entry-title') else "標題未找到"

    date_span = soup.find('span', class_='head', string='發布日期')
    date = date_span.find_next_sibling('span', class_='body').text.strip() if date_span else "日期未找到"

    author_span = soup.find('span', class_='head', string='作者')
    author = author_span.find_next_sibling('span', class_='body').text.strip() if author_span else "作者未找到"

    content_div = soup.find('div', class_='indent')
    content = ' '.join([p.text for p in content_div.find_all('p')]) if content_div else "內容未找到"

    return {
        'Title': title,
        'Date': date,
        'Author': author,
        'Content': content
    }


# `get_article_urls` 函數用於抓取網頁地圖中每篇文章的 URL。
# 此函數首先嘗試發起對網頁地圖網址的 GET 請求。如果此請求的 HTTP 狀態碼不為200，則回傳一個 leeg list。
# 如果 HTTP 狀態碼為200，則函數將嘗試從回應內容中解析 XML。
# 如果解析失敗，則回傳一個 leeg list。
# 如果解析成功，則函數將尋找並取出網頁地圖 URL，並加入到 URLs 列表。
# 最後函數回傳剛才抓取的所有文章的 URL。
def get_article_urls(sitemap_url):
    print(f"正在獲取 sitemap: {sitemap_url}")
    response = requests.get(sitemap_url)
    if response.status_code != 200:
        print(f"獲取 sitemap 失敗。狀態碼：{response.status_code}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        print(f"解析 XML 時出錯：{e}")
        return []

    namespaces = {
        'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
    }

    urls = []
    for url in root.findall('sm:url', namespaces):
        loc = url.find('sm:loc', namespaces)
        if loc is not None:
            urls.append(loc.text)

    print(f"找到 {len(urls)} 個文章 URL")
    return urls


# 定義 flatten_list_recursive 函數，用於將傳入的嵌套列表進行扁平化
# 嵌套列表是指列表內還包含列表的結構，例如 [1, 2, [3, 4, [5, 6]]]
# 扁平化是指將嵌套結構打平，變為一維結構，例如將上述列表扁平化會得到 [1, 2, 3, 4, 5, 6]
# 這個函數接收一個嵌套列表作為輸入，然後逐層解析列表元素
# 如果元素仍然是列表，則繼續對該元素進行解析直到最底層
# 將逐層解析出來的元素加入到結果列表中
# 最後返回扁平化後的一維列表
def flatten_list_recursive(nested_list):
    flattened = []
    for item in nested_list:
        if isinstance(item, list):
            flattened.extend(flatten_list_recursive(item))
        else:
            flattened.append(item)
    return flattened

# `process_and_save_articles` 函數將從每個 URL 提取的文章内容存儲到 CSV 檔案中。
# 由於我們可能有大量的 URL，為了防止我們一次性送出大量的請求並可能造成被伺服器封鎖，
# 我們在此使用了批量處理的策略。批量處理的含義是我們每次只處理一小部分 URL，
# 這通常也可提高處理效率。
#
# 參數:
# `flattened_urls`: 包含所有我們欲爬取的文章 URL 的列表。
# `batch_size`: 每個批次處理的 URL 數量。
#
# 此函數首先創建一個CSV檔案，並寫入表頭。
# 然後，它將預備處理的 URL 列表分成多個批次，每個批次的大小由參數決定。
# 對於每個批次，我們都會對其中的每個 URL 進行處理，並使用我們在之前定義的 `scrape_article` 函數提取文章內容。
# 提取的文章資訊將被添加到列表中，之後將被寫入到 CSV 檔案中。
# 在每次請求之間，我們會暫停一秒以避免對伺服器產生過大的壓力。
# 最後，所有的文章資訊都將被寫入到 CSV 檔案中。
#
# 請注意這個函數並未有回傳值，它的結果將直接儲存到硬碟中。
def process_and_save_articles(flattened_urls, batch_size=10, progress_callback=None):
    all_articles = []
    total = len(flattened_urls)
    total = 10
    for i in range(0, total, batch_size):
        batch = flattened_urls[i:i + batch_size]
        articles = []

        for j, url in enumerate(batch):
            article = scrape_article(url)
            articles.append(article)

            # 報告進度
            if progress_callback:
                overall_progress = (i + j + 1) / total
                message = f"已爬取: {article['Date']} : {article['Title']}"
                # print( message )
                progress_callback(overall_progress, message)

            time.sleep(1)  # 添加延遲以避免過快請求

        all_articles.extend(articles)


    # 將所有文章轉換為 DataFrame
    df = pd.DataFrame(all_articles)

    # 確保 DataFrame 包含所需的列
    required_columns = ['Title', 'Date', 'Author', 'Content', 'StockContent', 'Score']
    for col in required_columns:
        if col not in df.columns:
            df[col] = None  # 如果缺少某列，添加一個空列

    # 如果 StockContent 不存在或為空，添加一個空列表
    if 'StockContent' not in df.columns or df['StockContent'].isnull().all():
        df['StockContent'] = df['StockContent'].apply(lambda x: [] if pd.isnull(x) else x)

    return df

def get_article_urls_in_date(sitemap_url,start_date, end_date):
    start_date = start_date # 设置开始日期
    today = end_date
    today = pd.to_datetime(today)
    end_date = today + pd.offsets.MonthEnd(0)
    urls = parse_sitemap(sitemap_url, start_date, end_date)

    pt = []

    for url in urls:
        pt.append(get_article_urls(url))

    all_pt_urls = flatten_list_recursive(pt)

    print( len(all_pt_urls))
    return all_pt_urls

def run_scraper(sitemap_url, start_date, end_date, progress_callback=None):
    all_pt_urls = get_article_urls_in_date(sitemap_url, start_date, end_date)
    return process_and_save_articles(all_pt_urls, batch_size=10, progress_callback=progress_callback)
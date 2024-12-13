from .scraper import (
    parse_sitemap,
    scrape_article,
    get_article_urls,
    flatten_list_recursive,
    process_and_save_articles,
    get_article_urls_in_date,
    run_scraper
)

__all__ = [
    'parse_sitemap',
    'scrape_article',
    'get_article_urls',
    'flatten_list_recursive',
    'process_and_save_articles',
    'get_article_urls_in_date',
    'run_scraper'
]

__version__ = "1.0.0"
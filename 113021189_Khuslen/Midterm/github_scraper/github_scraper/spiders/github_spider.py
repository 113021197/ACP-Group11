import scrapy
import re
from ..items import RepositoryItem

class GithubSpiderSpider(scrapy.Spider):
    name = 'github_spider'
    start_urls = ['https://github.com/113021189?tab=repositories']
    
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'FEEDS': {
            'repositories.xml': {
                'format': 'xml',
                'item_element': 'repository',
                'root_element': 'repositories',
                'overwrite': True
            }
        },
        'DOWNLOAD_DELAY': 2,
        'FEED_EXPORT_ENCODING': 'utf-8'
    }

    def parse(self, response):
        # Extract repositories from current page
        repos = response.css('div[data-turbo-frame="repo-list-turbo-frame"] li')
        if not repos:
            self.logger.error("No repositories found! Check CSS selectors")
            
        for repo in repos:
            item = RepositoryItem(
                url=response.urljoin(repo.css('a[itemprop="name codeRepository"]::attr(href)').get()),
                about=(repo.css('p[itemprop="description"]::text').get() or '').strip(),
                last_updated=repo.css('relative-time::attr(datetime)').get()
            )
            
            # Improved empty repo detection
            is_empty = "This repository is empty" in repo.get()
            
            if not item.about and not is_empty:
                item.about = repo.css('a[itemprop="name codeRepository"]::text').get().strip()

            if is_empty:
                item.languages = None
                item.commits = None
                yield item
            else:
                yield response.follow(
                    item.url,
                    callback=self.parse_repository_details,
                    meta={'item': item},
                    dont_filter=True
                )

        # Enhanced pagination handling
        next_page = response.css('a[data-test-selector="pagination-next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

    def parse_repository_details(self, response):
        item = response.meta['item']
        
        # Language detection (updated for GitHub's 2024 layout)
        languages = response.css('li.d-inline[itemprop="keywords"] meta::attr(content)').getall()
        item.languages = languages or None

        # Commit count extraction (multiple fallbacks)
        commits_text = response.css('a.Link--primary[href*="/commits/"] strong::text').get()
        if not commits_text:
            commits_text = response.css('a[href*="/commits/"]::attr(aria-label)').re_first(r'\d+')
        if not commits_text:
            commits_text = response.xpath('//span[contains(text(),"commits")]/preceding-sibling::span/text()').get()
            
        item.commits = int(commits_text) if commits_text else 0

        yield item
# Scrapy settings for recolector project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "recolector"

SPIDER_MODULES = ["recolector.spiders"]
NEWSPIDER_MODULE = "recolector.spiders"

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "recolector (+http://www.yourdomain.com)"

ROBOTSTXT_OBEY = True
# Sustituir el contacto por el del grupo.
USER_AGENT = "RIWS-Crawler/1.0 (+mailto:grupo@example.org)"
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"
ITEM_PIPELINES = {
    "recolector.pipelines.RecursoPipeline": 300,
}
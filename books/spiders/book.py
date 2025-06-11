import scrapy
from scrapy.http import Response
import re


class BooksSpider(scrapy.Spider):
    name = "book"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response: Response, **kwargs) -> scrapy.Request:
        for book_pod in response.css(".product_pod"):
            title = book_pod.css("h3 a::attr(title)").get()
            price = book_pod.css("p.price_color::text").get().strip().replace("£", "")

            rating_classes = book_pod.css("p.star-rating::attr(class)").get()
            rating = (
                rating_classes.replace("star-rating ", "").strip()
                if rating_classes
                else None
            )

            relative_book_url = book_pod.css("h3 a::attr(href)").get()
            book_detail_url = response.urljoin(relative_book_url)

            yield scrapy.Request(
                url=book_detail_url,
                callback=self.parse_book_details,
                meta={
                    "title": title,
                    "price": price,
                    "rating": rating,
                },
            )

        next_page_link = response.css("li.next a::attr(href)").get()
        if next_page_link is not None:
            next_page_url = response.urljoin(next_page_link)
            yield scrapy.Request(url=next_page_url, callback=self.parse)

    def parse_book_details(self, response: Response, **kwargs) -> dict:
        title = response.meta["title"]
        price = response.meta["price"]
        rating = response.meta["rating"]

        upc = response.xpath("//th[text()='UPC']/following-sibling::td/text()").get()

        amount_in_stock = None

        stock_info_elements = response.css(".product_main .availability::text").getall()

        full_stock_text = " ".join(
            [text.strip() for text in stock_info_elements if text.strip()]
        )

        match = re.search(r"\((\d+)\s+available\)", full_stock_text)
        if match:
            amount_in_stock = int(match.group(1))

        category = response.css(".breadcrumb li:nth-child(3) a::text").get()

        description_selector = response.xpath(
            "//div[@id='product_description']/following-sibling::p/text()"
        )
        description = (
            description_selector.get().strip() if description_selector.get() else None
        )

        yield {
            "title": title,
            "price": price,
            "amount_in_stock": amount_in_stock,
            "rating": rating,
            "category": category,
            "description": description,
            "upc": upc,
        }

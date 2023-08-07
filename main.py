"""Pubu PoC main file"""
from PubuPoC import BookCrawler, PageCrawler

page_crawler = PageCrawler("data/pubu.db", "data/")
book_crawler = BookCrawler("data/pubu.db")
page_crawler.start()
book_crawler.start()

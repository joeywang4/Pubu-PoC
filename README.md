# Pubu PoC

[中文版說明文件連結](README-TW.md)

A proof-of-concept implementation of the vulnerability [ZD-2023-00144](https://zeroday.hitcon.org/vulnerability/ZD-2023-00144), which allows an attacker to download books from [pubu.com.tw](https://www.pubu.com.tw/) without buying them.
For more information, please refer to this [blog post](https://joeywang.tw/blog/pubu-vulnerability/).

**Please note⚠️**: This is only a demonstration and for educational purposes only. Downloading copyrighted materials may violate the law or the website's Terms of Service. **Use at your own risk.**

## Demo

[![Watch the video](https://img.youtube.com/vi/f496UUln1z0/0.jpg)](https://youtu.be/f496UUln1z0)

## Usage

This repo requires `python3` (version >= 3.8) and some additional packages.

1. Clone this repo: `git clone https://github.com/joeywang4/Pubu-PoC`
2. Change to the cloned directory: `cd Pubu-PoC`
3. Install required packages: `pip install -r requirements.txt`
4. Download a list of books: `python main.py -v [book_id ...]`
5. Find the book at the `output/` folder.

`book_id` is a number that represents a book's ID, which can be found in the URL of the book.
For example, the book URL `https://www.pubu.com.tw/ebook/999` indicates that this book's `book_id` is `999`. Therefore, to download this book, execute `python main.py -v 999`.

### Command line arguments

`main.py` accepts several arguments to execute on different modes or output to different folders. The followings are some useful arguments, and please execute `python main.py -h` for the complete list of arguments.

- `-v` or `--verbose`: generate verbose output
- `-t` or `--threads`: adjust the number of threads for the crawler
- `-o` or `--output`: configure the path to the output directory (default to `output/`)
- `-c` or `--change-decode`: adjust the decode method when generating the PDF file. This option is required if the downloaded book is decoded incorrectly.

### Known issues

1. Incorrect pages: sometimes books are decoded incorrectly, and the pages will look like tiles that are composed in a weird order. In this case, execute `main.py` with the `-c` option.
2. Searching never ends: some book's pages are not continuous and can be difficult to search. Please be patient or [pre-fetch the pages](#local-database) (also takes a lot of time!) before downloading the book.

## Local database

When downloading a book, this program will try to search the pages online, and sometimes searching can be very time-consuming. This program can pre-fetch the pages into a local database, and so the searching step can be skipped when downloading a book.

To pre-fetch the pages, execute `python main.py -u pages`, or use the `-u all` option to also pre-fetch the books. For more information about the local database, please refer to [this file](database.md).

Please note that pre-fetching the up-to-date data can take a very long time, and the local database will consume around 1G of storage.

## Testing

The test files are located at `test/`. Run `pytest` to execute them.

## Contribution

PRs are welcome! Please run [black](https://github.com/psf/black) and [pylint](https://www.pylint.org/) after making changes to the code and add test cases for them if possible.

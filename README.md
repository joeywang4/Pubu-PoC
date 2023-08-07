# Pubu PoC

## Database

### `books` table
1. id: The book's id (int), as indicated by the book's url (`https://www.pubu.com.tw/ebook/[book_id]`). 
2. documentId: The book's document id (int).
3. title: The book's title (text).
4. pages: Number of pages (int).
5. author: The book's author (text).
6. cover: The url of the book's cover image (text).
7. price: The book's price (int).
8. publisher: The book's publisher (text).
9. type: The book's category (text).
10. error: Error code when fetching the book.

### `pages` table
Store the pages of a book. The pages are stored in a compact format, which removes most metadata of the pages.

1. documentId: The book's document id (int).
2. pagesBlob: The encoded and compressed urls of the pages of a book (blob).

### `extensions` table
A fixed table that records the file extension of pages.

| id | ext |
| -- | --- |
| 1 | .jpg |

### `fronts` table
A fixed table that records the front of a page's url.

| front | enum |
| ----- | :--: |
| "duyldfll42se2" | 0 |
| "d3lcxj447n2nux" | 1 |
| "d24p424bn3x9og" | 2 |
| "d3rhh0yz0hi1gj" | 3 |

### `states` table
Records the latest page id recorded in `pages`.

| id | data |
| -- | ---- |
| 0  | page id |

## Raw pages
Store the metadata of each page, including error pages. Each file `[i].bin` stores 1M pages, compressed by zlib. Each page is encoded as 16 bytes data, with the following structure:

1. Byte 0 ~ 4: Page id
2. Byte 4 ~ 8: Document id
3. Byte 8 ~ 9: file extension (4 bits) || front of the domain name (4 bits)
4. Byte 9 ~ 16: filename (or HTTP error code) padded with null bytes

# PUBU PoC

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

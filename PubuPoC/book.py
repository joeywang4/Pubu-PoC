"""Book class"""


class Book:
    """A metadata of a book"""

    def __init__(self) -> None:
        """Create an empty book"""
        self.book_id = 0
        self.doc_id = 0
        self.title = ""
        self.pages = 0
        self.author = ""
        self.cover = ""
        self.price = 0
        self.publisher = ""
        self.type = ""
        self.error = 0

    def to_tuple(self) -> tuple:
        """
        Put this book's metadata in a tuple.
        Useful when inserting to DB.
        """
        return (
            self.book_id,
            self.doc_id,
            self.title,
            self.pages,
            self.author,
            self.cover,
            self.price,
            self.publisher,
            self.type,
            self.error,
        )

    @classmethod
    def from_tuple(cls, data: tuple) -> "Book":
        """
        Generate a book from metadata in a tuple.
        Useful when querying from DB.
        """
        book = cls()

        book.book_id = data[0]
        book.doc_id = data[1]
        book.title = data[2]
        book.pages = data[3]
        book.author = data[4]
        book.cover = data[5]
        book.price = data[6]
        book.publisher = data[7]
        book.type = data[8]
        book.error = data[9]

        return book

    def merge(self, existing: "Book") -> None:
        """
        Extend this book with additional data.
        `error` is set to 0 when `doc_id` is no longer 0.
        Modify other fields when they contain the default value.
        """
        if self.book_id == 0 and existing.book_id != 0:
            self.book_id = existing.book_id

        if self.doc_id == 0 and existing.doc_id != 0:
            self.doc_id = existing.doc_id

        if self.title == "" and existing.title != "":
            self.title = existing.title

        if self.pages == 0 and existing.pages != 0:
            self.pages = existing.pages

        if self.author == "" and existing.author != "":
            self.author = existing.author

        if self.cover == "" and existing.cover != "":
            self.cover = existing.cover

        if self.price == 0 and existing.price != 0:
            self.price = existing.price

        if self.publisher == "" and existing.publisher != "":
            self.publisher = existing.publisher

        if self.type == "" and existing.type != "":
            self.type = existing.type

        # a book never turns to error
        if self.error != 0 and self.doc_id != 0:
            self.error = 0

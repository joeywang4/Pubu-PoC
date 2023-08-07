"""Test the `Book` class"""
from PubuPoC import Book

SAMPLE_TUPLE = (
    12345,  # book_id
    54321,  # doc_id
    "abcde",  # title
    123,  # pages
    "zxcv",  # author
    "qwer",  # cover
    1234,  # price
    "yuio",  # publisher
    "rweur",  # type
    0,  # error
)


def sample_book() -> Book:
    """Generate a sample book"""
    book = Book()
    book.book_id = 12345
    book.doc_id = 54321
    book.title = "abcde"
    book.pages = 123
    book.author = "zxcv"
    book.cover = "qwer"
    book.price = 1234
    book.publisher = "yuio"
    book.type = "rweur"
    return book


def book_eq(book1: Book, book2: Book):
    """Check two books are the same"""
    assert book1.book_id == book2.book_id, "book_id mismatch"
    assert book1.doc_id == book2.doc_id, "doc_id mismatch"
    assert book1.title == book2.title, "title mismatch"
    assert book1.pages == book2.pages, "pages mismatch"
    assert book1.author == book2.author, "author mismatch"
    assert book1.cover == book2.cover, "cover mismatch"
    assert book1.price == book2.price, "price mismatch"
    assert book1.publisher == book2.publisher, "publisher mismatch"
    assert book1.type == book2.type, "type mismatch"
    assert book1.error == book2.error, "error mismatch"


def test_to_tuple():
    """Test to_tuple generates a correct tuple"""
    book = sample_book()
    assert book.to_tuple() == SAMPLE_TUPLE


def test_from_tuple():
    """Test from_tuple generates a correct book"""
    book = Book.from_tuple(SAMPLE_TUPLE)
    book_eq(book, sample_book())


def test_merge():
    """Test merge extends a book correctly"""
    book1 = sample_book()
    book2 = Book()
    book2.error = 404

    # error code shouldn't be merged
    book1.merge(book2)
    book_eq(book1, sample_book())

    # error code should be erased
    book2.merge(book1)
    book_eq(book1, book2)

    # existing attribute should be preserved
    book3 = Book()
    book3.book_id = 333
    book3.doc_id = 333
    book3.title = "3333"
    book3.pages = 333
    book3.author = "3333"
    book3.cover = "333"
    book3.price = 333
    book3.publisher = "333"
    book3.type = "33333"
    book4 = sample_book()
    book4.merge(book3)
    book_eq(book4, sample_book())

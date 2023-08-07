"""Test the `Page` class"""
from pathlib import Path
from zlib import compress
import pytest
from PubuPoC import Page, RawPages, to_blob, from_blob

SAMPLE_URL = "https://duyldfll42se2.cloudfront.net/docs/54321/abcdef.jpg"
SAMPLE_BIN = b"\x39\x30\x00\x00\x31\xd4\x00\x00\x10abcdef\x00"
SAMPLE_COMPACT = SAMPLE_BIN[8:15]


class DB:
    """Fake DB for testing"""

    def __init__(self) -> None:
        self.id_ext = {1: ".jpg"}
        self.ext_id = {".jpg": 1}
        self.id_front = {
            0: "duyldfll42se2",
            1: "d3lcxj447n2nux",
            2: "d24p424bn3x9og",
            3: "d3rhh0yz0hi1gj",
        }
        self.front_id = {}
        for _k, _v in self.id_front.items():
            self.front_id[_v] = _k


def sample_page() -> Page:
    """Generate a sample page"""
    return Page(12345, 54321, 1, 0, "abcdef")


def page_eq(page1: Page, page2: Page) -> bool:
    """Return page1 == page2"""
    assert page1.page_id == page2.page_id, "page_id mismatch"
    assert page1.doc_id == page2.doc_id, "doc_id mismatch"
    assert page1.ext_id == page2.ext_id, "ext_id mismatch"
    assert page1.front_id == page2.front_id, "front_id mismatch"
    assert page1.filename == page2.filename, "filename mismatch"
    assert page1.error == page2.error, "error mismatch"


def test_to_bin():
    """Test to_bin generates correct data"""
    page = sample_page()
    got = page.to_bin()

    assert got == SAMPLE_BIN


def test_from_bin():
    """Test from bin generates a correct page"""
    page = Page.from_bin(SAMPLE_BIN)
    page_eq(page, sample_page())


def test_to_url():
    """Test to_url generates a correct url"""
    page = sample_page()
    _db = DB()
    assert page.to_url(_db) == SAMPLE_URL


def test_from_url():
    """Test from_url generates a correct page"""
    _db = DB()
    page = Page.from_url(SAMPLE_URL, _db, 12345)
    page_eq(page, sample_page())


def test_to_compact():
    """Test to_compact generates correct data"""
    page = sample_page()
    assert page.to_compact() == SAMPLE_COMPACT


def test_from_compact():
    """Test from_compact generates a correct page"""
    page = Page.from_compact(SAMPLE_COMPACT, 12345, 54321)
    page_eq(page, sample_page())


# Raw Pages


def test_get(tmp_path: Path):
    """Test load file for RawPages"""
    path = tmp_path.as_posix()
    raw_pages = RawPages(path)

    page = sample_page()
    data = b""
    page.page_id = 0
    data += page.to_bin()
    data += b"\x00" * raw_pages.record_size * (raw_pages.record_count - 1)
    with open(path + "/0.bin", "wb") as ofile:
        ofile.write(compress(data))

    # test read file correctly
    got = raw_pages.get(0)
    assert got == data

    # test create new file correctly
    got = raw_pages.get(1)
    assert got == b"\x00" * raw_pages.record_size * raw_pages.record_count

    # test files are cached
    assert 0 in raw_pages.opened_raw
    assert 1 in raw_pages.opened_raw

    # test cache can be overwritten
    page.page_id = 2
    raw_pages.get(0)[
        2 * raw_pages.record_size : 3 * raw_pages.record_size
    ] = page.to_bin()
    got = raw_pages.get(0)[2 * raw_pages.record_size : 3 * raw_pages.record_size]
    assert got == page.to_bin()

    # test files with smallest file_id are closed
    for i in range(2, raw_pages.max_opened + 2):
        raw_pages.get(i)
    assert 0 not in raw_pages.opened_raw, f"0 is in {raw_pages.opened_raw.keys()}"
    assert 1 not in raw_pages.opened_raw, f"1 is in {raw_pages.opened_raw.keys()}"


def test_load_page(tmp_path: Path):
    """Test load page from RawPages"""
    path = tmp_path.as_posix()
    raw_pages = RawPages(path)

    page = sample_page()
    # write page 3
    data = b"\x00" * raw_pages.record_size * 3
    page.page_id = 3
    data += page.to_bin()
    data += b"\x00" * raw_pages.record_size * (raw_pages.record_count - 4)
    with open(path + "/0.bin", "wb") as ofile:
        ofile.write(compress(data))

    # write page 5000001
    page2 = sample_page()
    page2.page_id = (raw_pages.record_count * 5) + 1
    data = b"\x00" * raw_pages.record_size
    data += page2.to_bin()
    data += b"\x00" * raw_pages.record_size * (raw_pages.record_count - 2)
    with open(path + "/5.bin", "wb") as ofile:
        ofile.write(compress(data))

    # test pages are loaded correctly
    page_eq(page, raw_pages.load_page(3))
    page_eq(page2, raw_pages.load_page(page2.page_id))

    # test None is returned for non-exist page
    assert raw_pages.load_page(1) is None
    assert raw_pages.load_page(12345) is None


def test_write_page(tmp_path: Path):
    """Test write page for RawPages"""
    path = tmp_path.as_posix()
    raw_pages = RawPages(path)

    page = sample_page()
    page.page_id = 123

    # test page is written correctly
    raw_pages.write_page(page)
    offset = page.page_id * raw_pages.record_size
    assert (
        page.to_bin()
        == raw_pages.opened_raw[0][offset : offset + raw_pages.record_size]
    )


def test_close_single(tmp_path: Path):
    """Test close a sigle file of RawPages"""
    path = tmp_path.as_posix()
    raw_pages = RawPages(path)

    page = sample_page()
    # write page 3
    data = b"\x00" * raw_pages.record_size * 3
    page.page_id = 3
    data += page.to_bin()
    data += b"\x00" * raw_pages.record_size * (raw_pages.record_count - 4)
    data = compress(data)

    # test file is written after close
    raw_pages.write_page(page)
    raw_pages.close_single(0)
    with open(path + "/0.bin", "rb") as infile:
        got = infile.read()
    assert data == got

    # test file is not cached
    assert 0 not in raw_pages.opened_raw.keys()

    # test not opened file cannot be closed
    with pytest.raises(AssertionError):
        raw_pages.close_single(0)


def test_close(tmp_path: Path):
    """Test close all files of RawPages"""
    path = tmp_path.as_posix()
    raw_pages = RawPages(path)

    # test cache is empty after close
    for i in range(raw_pages.max_opened):
        raw_pages.get(i)
    raw_pages.close()
    assert len(raw_pages.opened_raw.keys()) == 0


def test_blob_conversion():
    """Test to_blob and from_blob generate correct pages"""
    test_size = 10
    pages = [sample_page() for _ in range(test_size)]
    for i in range(test_size):
        pages[i].page_id = 0
        pages[i].ext_id = i % 4
        pages[i].filename = f"ab{i}def"

    blob = to_blob(pages)
    assert isinstance(blob, bytes)

    new_pages = from_blob(blob, pages[0].doc_id)
    for i in range(test_size):
        page_eq(pages[i], new_pages[i])

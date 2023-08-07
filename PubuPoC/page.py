"""Managing pages"""
from urllib.parse import urlparse
from zlib import compress, decompress
from os.path import isfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .db import DB


class Page:
    """A page url"""

    def __init__(
        self,
        page_id: int = 0,
        doc_id: int = 0,
        ext_id: int = 0,
        front_id: int = 0,
        filename: str = "",
        error: int = 0,
    ) -> None:
        self.page_id = page_id
        self.doc_id = doc_id
        self.ext_id = ext_id
        self.front_id = front_id
        self.filename = filename
        self.error = error

    def to_bin(self) -> bytes:
        """
        Pack page into 16 bytes of data
        0 ~ 4: Page id (real id)
        4 ~ 8: Document id
        8 ~ 9: file extension (4 bits) || front of the domain name (4 bits)
        9 ~ 16: filename (or HTTP error code)
        """
        output = b""
        output += int.to_bytes(self.page_id, 4, "little")
        output += int.to_bytes(self.doc_id, 4, "little")
        output += int.to_bytes(self.front_id + (self.ext_id << 4), 1, "little")
        text = str(self.error) if self.error > 0 else self.filename
        output += text.encode().ljust(7, b"\x00")
        return output

    @classmethod
    def from_bin(cls, data: bytes):
        """
        Construct a page from binary data
        """
        page_id = int.from_bytes(data[0:4], "little")
        doc_id = int.from_bytes(data[4:8], "little")
        ext_id = data[8] >> 4
        front_id = data[8] & 0xF
        filename = ""
        error = 0
        if doc_id != 0:
            filename = data[9:].strip(b"\x00").decode()
        else:
            error = int(data[9:].strip(b"\x00").decode())

        return cls(page_id, doc_id, ext_id, front_id, filename, error)

    def to_url(self, database: "DB") -> str:
        """
        Generate page url
        """
        assert self.front_id in database.id_front
        assert self.ext_id in database.id_ext
        assert self.error == 0

        url = "https://"
        url += database.id_front[self.front_id]
        url += ".cloudfront.net/docs/"
        url += str(self.doc_id)
        url += "/"
        url += self.filename
        url += database.id_ext[self.ext_id]

        return url

    @classmethod
    def from_url(cls, url: str, database: "DB", page_id: int = 0):
        """
        Construct a Page from url
        """
        # parse the elements in url
        url = urlparse(url)
        front = url.netloc
        front = front[: front.find(".")]
        path = url.path.split("/")[1:]
        doc_id = int(path[1])
        filename = path[2]
        ext_loc = filename.find(".")
        filename, ext = filename[:ext_loc], filename[ext_loc:].lower()

        # load the id of front and extension
        if front not in database.front_id:
            print(f"[!] Page {page_id} error")
            print(f"[!] URL front {front} does not exist")
            front_id = len(database.front_id.keys()) + 1
        else:
            front_id = database.front_id[front]

        if ext not in database.ext_id:
            print(f"[!] Page {page_id} error")
            print(f"[!] Extension {ext} does not exist")
            ext_id = len(database.ext_id.keys()) + 1
        else:
            ext_id = database.ext_id[ext]

        return cls(page_id, doc_id, ext_id, front_id, filename, 0)

    def to_compact(self) -> bytes:
        """
        Pack page into 7 bytes data
        Only saves ext_id, front_id, and filename
        0 ~ 1: file extension (4 bits) || front of the domain name (4 bits)
        1 ~ 7: filename
        """
        assert len(self.filename) == 6

        output = int.to_bytes(self.front_id + (self.ext_id << 4), 1, "little")
        return output + self.filename.encode()

    @classmethod
    def from_compact(cls, data: bytes, page_id: int = 0, doc_id: int = 0):
        """
        Construct a page from compact data
        """
        ext_id = data[0] >> 4
        front_id = data[0] & 0xF
        filename = data[1:].decode()

        return cls(page_id, doc_id, ext_id, front_id, filename)


class RawPages:
    """Manage raw page records"""

    def __init__(self, path: str = "data/") -> None:
        self.path = path
        self.opened_raw = {}
        self.record_size = 16
        self.record_count = 1000000
        self.max_opened = 3
        self.max_loaded_pages = 3 * self.record_count

    def get(self, file_id: int) -> bytearray:
        """Load a raw file from `path` and cache in `opened_raw`"""
        if file_id in self.opened_raw:
            return self.opened_raw[file_id]

        # close a file when too many files are opened
        keys = self.opened_raw.keys()
        if len(keys) >= self.max_opened:
            self.close_single(min(keys))

        # load raw file or create one
        filename = self.path + f"/{file_id}.bin"
        if isfile(filename):
            with open(filename, "rb") as infile:
                self.opened_raw[file_id] = bytearray(decompress(infile.read()))
        else:
            # create a new bytearray of `record_size` * `record_count`
            size = self.record_size * self.record_count
            self.opened_raw[file_id] = bytearray(b"\x00" * size)

        return self.opened_raw[file_id]

    def load_page(self, page_id: int) -> Page or None:
        """Load a page from raw records. Return None if not exist."""
        file_id = page_id // self.record_count
        offset = self.record_size * (page_id % self.record_count)
        got = self.get(file_id)[offset : offset + self.record_size]

        return None if (got == b"\x00" * self.record_size) else Page.from_bin(got)

    def write_page(self, page: Page) -> None:
        """Write a page to raw records"""
        file_id = page.page_id // self.record_count
        offset = self.record_size * (page.page_id % self.record_count)
        self.get(file_id)[offset : offset + self.record_size] = page.to_bin()

    def close_single(self, file_id: int) -> None:
        """Close a single file"""
        assert file_id in self.opened_raw
        with open(self.path + f"/{file_id}.bin", "wb") as ofile:
            ofile.write(compress(self.opened_raw[file_id]))
        del self.opened_raw[file_id]

    def close(self) -> None:
        """Close opened raw files"""
        opened = list(self.opened_raw.keys())
        for file_id in opened:
            self.close_single(file_id)

    def sync_db(self, database: "DB") -> None:
        """Sync raw pages into DB"""
        curr_page_id = database.get_last_page_id() + 1
        new_pages = []
        while (new_page := self.load_page(curr_page_id)) is not None:
            # ignore error pages
            if new_page.error == 0:
                new_pages.append(new_page)
            curr_page_id += 1

            # save pages to DB when too many loaded pages
            if len(new_pages) >= self.max_loaded_pages:
                database.save_pages(new_pages)
                new_pages = []

        if len(new_pages) > 0:
            database.save_pages(new_pages)


# Handle multiple pages


def from_blob(blob: bytes, doc_id: int = 0) -> list[Page]:
    """
    Decompress a blob and decode to pages
    """
    output = []
    blob = decompress(blob)
    assert len(blob) % 7 == 0

    for i in range(0, len(blob), 7):
        output.append(Page.from_compact(blob[i : i + 7], 0, doc_id))

    return output


def to_blob(pages: list[Page]) -> bytes:
    """
    Encode pages and compress into blob
    """
    output = b""

    for page in pages:
        output += page.to_compact()

    output = compress(output)
    return output

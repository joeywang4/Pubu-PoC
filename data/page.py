"""Managing pages"""
from urllib.parse import urlparse
from zlib import compress, decompress


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

    def to_url(self, _db) -> str:
        """
        Generate page url
        """
        assert self.front_id in _db.id_front
        assert self.ext_id in _db.id_ext
        assert self.error == 0

        url = "https://"
        url += _db.id_front[self.front_id]
        url += ".cloudfront.net/docs/"
        url += str(self.doc_id)
        url += "/"
        url += self.filename
        url += _db.id_ext[self.ext_id]

        return url

    @classmethod
    def from_url(cls, url: str, _db, page_id: int = 0):
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
        if front not in _db.front_id:
            print(f"[!] Page {page_id} error")
            print(f"[!] URL front {front} does not exist")
            front_id = len(_db.front_id.keys()) + 1
        else:
            front_id = _db.front_id[front]

        if ext not in _db.ext_id:
            print(f"[!] Page {page_id} error")
            print(f"[!] Extension {ext} does not exist")
            ext_id = len(_db.ext_id.keys()) + 1
        else:
            ext_id = _db.ext_id[ext]

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

"""Leitura de ZIP remoto via HTTP Range (lista e extrai membros sem baixar o arquivo inteiro)."""
import io, zipfile, requests


class HttpFile(io.RawIOBase):
    def __init__(self, url, session=None):
        self.url, self.s, self.pos = url, session or requests.Session(), 0
        self.size = int(self.s.head(url, timeout=120, allow_redirects=True).headers["Content-Length"])

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = {0: off, 1: self.pos + off, 2: self.size + off}[whence]
        return self.pos

    def read(self, n=-1):
        if n is None or n < 0: n = self.size - self.pos
        if n == 0 or self.pos >= self.size: return b""
        end = min(self.pos + n, self.size) - 1
        r = self.s.get(self.url, headers={"Range": f"bytes={self.pos}-{end}"}, timeout=600)
        r.raise_for_status()
        self.pos += len(r.content)
        return r.content

    def readinto(self, b):
        data = self.read(len(b)); b[:len(data)] = data; return len(data)


def open_remote_zip(url):
    return zipfile.ZipFile(io.BufferedReader(HttpFile(url), buffer_size=1 << 20))

from .exceptions import *
from .structures import CaseInsensitiveDict
from .models import Response
from urllib.parse import urlsplit
import brotli, gzip, socks, socket, ssl, zlib

scheme_to_proxy_type = {
    'http': socks.HTTP, 'https': socks.HTTP,
    'socks': socks.SOCKS4, 'socks4': socks.SOCKS4,
    'socks5': socks.SOCKS5, 'socks5h': socks.SOCKS5
}

scheme_to_port = {
    'http': 80,
    'https': 443,
    'socks': 1080, 'socks4': 1080, 'socks5': 1080
}

class Session:
    def __init__(self, proxies={}, timeout=60, chunk_size=(1024 ** 2), decode_content=True, verify=True, ciphers=None):
        if proxies:
            for scheme, proxy_url in proxies.items():
                proxy = urlsplit(proxy_url)
                if scheme not in scheme_to_port:
                    raise UnsupportedScheme("'{}' is not a supported scheme".format(scheme))
                if proxy.scheme not in scheme_to_proxy_type:
                    raise UnsupportedScheme(
                        f"'{proxy.scheme}' is not a supported proxy scheme")
                proxies[scheme] = proxy
        
        self.ciphers = ciphers
        self.timeout = timeout
        self.max_chunk_size = chunk_size
        self.decode_content = decode_content
        self.verify = verify
        self._scheme_to_proxy = proxies
        self._addr_to_conn = {}
        self._verified_context = ssl.create_default_context()
        self._unverified_context = ssl._create_unverified_context()
                
    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.clear()

    def clear(self):
        addrs = list(self._addr_to_conn)
        while addrs:
            addr = addrs.pop()
            sock = self._addr_to_conn[addr]
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            sock.close()
            self._addr_to_conn.pop(addr, None)

    def request(self, method, url, headers=None, data=None, timeout=None,
                version='1.1', verify=None, ciphers=None):
        ciphers = ciphers if ciphers is not None else self.ciphers
        parsed_url = urlsplit(url)

        if parsed_url.scheme not in scheme_to_port:
            raise UnsupportedScheme(
                f"'{parsed_url.scheme}' is not a supported scheme")
        
        if not verify: verify = self.verify

        if not isinstance(headers, CaseInsensitiveDict):
            headers = CaseInsensitiveDict(headers)

        if not 'Host' in headers:
            headers["Host"] = parsed_url.hostname

        if data:
            if not isinstance(data, bytes):
                data = data.encode("utf-8")

            if 'Content-Length' not in headers:
                headers["Content-Length"] = int(len(data))

        host_addr = (
            parsed_url.hostname.lower(),
            parsed_url.port or scheme_to_port[parsed_url.scheme]
        )
        conn_reused = host_addr in self._addr_to_conn

        request = self._prepare_request(
            method=method,
            path=('{}?{}'.format(parsed_url.path, parsed_url.query) or '') or "/",
            version=version,
            headers=headers,
            body=data
        )

        while True:
            try:
                conn = self._addr_to_conn.get(host_addr)
                if conn:
                    if timeout is not None:
                        conn.settimeout(timeout)
                else:
                    conn = self._create_socket(
                        host_addr,
                        proxy=self._scheme_to_proxy.get(parsed_url.scheme),
                        timeout=timeout if timeout is not None \
                                else self.timeout,
                        ssl_wrap=('https' == parsed_url.scheme),
                        ssl_verify=verify,
                        ciphers=ciphers)
                    self._addr_to_conn[host_addr] = conn
                
                conn.send(request)
                return self._get_response(conn, self.max_chunk_size,
                                            self.decode_content, method != "HEAD")

            except Exception as err:
                if host_addr in self._addr_to_conn:
                    self._addr_to_conn.pop(host_addr)

                if not conn_reused:
                    if not isinstance(err, RequestException):
                        err = RequestException(err)
                    raise err

                conn_reused = False
    def get(self, url, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def options(self, url, **kwargs):
        return self.request("OPTIONS", url, **kwargs)

    def head(self, url, **kwargs):
        return self.request("HEAD", url, **kwargs)

    def put(self, url, **kwargs):
        return self.request("PUT", url, **kwargs)

    def patch(self, url, **kwargs):
        return self.request("PATCH", url, **kwargs)

    def delete(self, url, **kwargs):
        return self.request("DELETE", url, **kwargs)

    def _create_socket(self, dest_addr, proxy=None, timeout=None, ssl_wrap=True, ssl_verify=True, remote_dns=False, ciphers=None):
        if proxy is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            sock = socks.socksocket()
            sock.set_proxy(
                scheme_to_proxy_type[proxy.scheme],
                addr=proxy.hostname,
                port=proxy.port,
                username=proxy.username,
                password=proxy.password,
                rdns=remote_dns
            )

        if timeout:
            sock.settimeout(timeout)

        sock.connect(dest_addr)

        if ssl_wrap:
            context = self._verified_context \
                      if ssl_verify else self._unverified_context
            if ciphers is not None:
                context.set_ciphers(ciphers)
            sock = context.wrap_socket(
                sock,
                server_hostname=dest_addr[0])

        return sock

    @staticmethod
    def _prepare_request(method, path, version, headers, body):
        request = "{} {} HTTP/{}\r\n".format(method, path, version)

        for header, value in headers.items():
            if value is None:
                continue
            request += "{}: {}\r\n".format(header, value)
        request += '\r\n'
        request = request.encode('UTF-8')

        if body: request += body

        return request

    @classmethod
    def _get_response(cls, conn, max_chunk_size, decode_content, get_content):
        resp = conn.recv(max_chunk_size)

        if not resp:
            raise EmptyResponse('Server returned an empty response.')

        while not b"\r\n\r\n" in resp:
            resp += conn.recv(max_chunk_size)

        resp, data = resp.split(b"\r\n\r\n", 1)
        resp = resp.decode()
        status, raw_headers = resp.split("\r\n", 1)
        version, status, message = status.split(" ", 2)

        headers = CaseInsensitiveDict()
        for header in raw_headers.splitlines():
            header, value = header.split(":", 1)
            value = value.lstrip(' ')
            if header in headers:
                if isinstance(headers[header], str):
                    headers[header] = [headers[header]]
                headers[header].append(value)
            else:
                headers[header] = value
        
        # download chunks until content-length is met
        if get_content:
            if 'content-length' in headers:
                goal = int(headers["content-length"])
                while goal > len(data):
                    chunk = conn.recv(min(goal-len(data), max_chunk_size))
                    if not chunk:
                        raise RequestException("Empty chunk")
                    data += chunk
            
            # download chunks until "0\r\n\r\n" is recv'd, then process them
            elif headers.get("transfer-encoding") == "chunked":
                if not data.endswith(b"0\r\n\r\n"):
                    while True:
                        chunk = conn.recv(max_chunk_size)
                        data += chunk
                        if not chunk or chunk.endswith(b"0\r\n\r\n"):
                            break

                raw = data
                data = b""
                while raw:
                    length, raw = raw.split(b"\r\n", 1)
                    length = int(length, 16)
                    chunk, raw = raw[:length], raw[length+2:]
                    data += chunk

            # download chunks until recv is empty
            else:
                while True:
                    chunk = conn.recv(max_chunk_size)
                    if not chunk:
                        break
                    data += chunk

        if "content-encoding" in headers and decode_content:
            data = cls._decode_content(data, headers["content-encoding"])

        return Response(int(status), message, headers, data)

    @staticmethod
    def _decode_content(content, encoding):
        if encoding == "br":
            content = brotli.decompress(content)
        elif encoding == "gzip":
            content = gzip.decompress(content)
        elif encoding == "deflate":
            content = zlib.decompress(content)
        else:
            raise UnsupportedEncoding('{} is not a valid encoding.'.format(encoding))

        return content

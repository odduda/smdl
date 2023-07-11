import json
import re
import socket

class Requests:
    
    def __init__(self):
        self.request = ""
        self.sock = socket.socket()
        self.method = None
        self.url = None
        self.port = 80
        self.url_extractor = r"(http[s]?:\/\/)?([^\/\s]+)(.*)"

    def _send(self):
        self.sock.send(self.request.encode())
        buff = bytearray(2048)
        response_length = 0
        while True:
            data = self.sock.readinto(buff, 2048)
            response_length += data
            if data == 0:
                break
        self.sock.close()
        data = buff[:response_length].decode()
        self._clean()
        return Response(data)

    def _init_head(self, host, path):
        self.request += f"{self.method} {path} HTTP/1.1\r\nHost: {host}\r\n"

    def _add_header(self, key, value):
        self.request += f"{key}: {value}\r\n"

    def _add_body(self, data):
        if self.method == "POST":
            self._add_header("Content-Type", "application/json")
            self._add_header("Content-Length", len(data))
        self.request+= f"\r\n{data}"
    
    def _clean(self):
        self.request = ""
        self.method = None
        self.url = None
        self.sock = socket.socket()
    
    def _connect_socket(self):
        sockaddr = socket.getaddrinfo(self.url, self.port)[0][-1]
        self.sock.connect(sockaddr)

    def parse_url(self, url):
        query = re.match(self.url_extractor, url)
        if not query:
            return False
        _, host, path = query.groups()
        self.url = host
        if not path:
            path = "/"
        return [host, path]
    
    def _method(self, url, port, data, method, headers={}):
        host, path = self.parse_url(url)
        self.port = port
        self.method = method
        self._init_head(host, path)
        self._connect_socket()
        print(self.request)
        if headers:
            for k, v in headers.items():
                self._add_header(k, v)
        if method == "POST":
            self._add_body(json.dumps(data))
        if method == "GET":
            self.request += "\r\n"
        response = self._send()
        return response

    def post(self, url, data, port=80, headers={}):
        try:
            return self._method(url, port, data, "POST", headers)
        except Exception:
            self._clean()
            return Response('HTTP/1.1 500 Internal Server Error\r\n\r\n')

    def get(self, url, port=80, headers={}):
        try:
            return self._method(url, port, None, "GET", headers)
        except Exception:
            self._clean()
            return Response('HTTP/1.1 500 Internal Server Error\r\n\r\n')

    

class Response:

    def __init__(self, data):
        self.head, self.body = data.split("\r\n\r\n")
        self._status = None
        self._headers = {}
        self._parse_headers()


    def _parse_headers(self):
        tmp = self.head.split("\r\n")
        self._status = int(tmp[0].split(" ")[1])
        for header in tmp[1:]:
            key, val = header.split(": ")
            self._headers[key] = val

    @property
    def status(self):
        return self._status

    @property
    def headers(self):
        return self._headers
    
    def json(self):
        data = False
        try:
            data = json.loads(self.body)
        except Exception:
            pass
        return data
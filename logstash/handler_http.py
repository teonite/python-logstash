from logging import Handler
import json
import sys

class HTTPLogstashHandler(Handler):
    """
    A class which sends records to a Web server, using POST semantics.
    """
    def __init__(self, host, port, url, secure=False, credentials=None,
                 context=None, tags=None):
        """
        Initialize the instance with the host, the request URL, and the method POST
        """
        super(HTTPLogstashHandler, self).__init__()
        if not secure and context is not None:
            raise ValueError("context parameter only makes sense "
                             "with secure=True")
        self.tags = tags
        self.port = port
        self.host = host
        self.url = url
        self.method = 'POST'
        self.secure = secure
        self.credentials = credentials
        self.context = context

    def mapLogRecord(self, record):
        """
        Default implementation of mapping the log record into a dict
        that is sent as the CGI data. Overwrite in your class.
        Contributed by Franz Glasner.
        """
        record_dict = record.__dict__
        record_dict.setdefault('tags', self.tags)
        return record_dict

    def convert_json_to_bytes(self, message):
        if sys.version_info < (3, 0):
            return json.dumps(message)
        else:
            return bytes(json.dumps(message), 'utf-8')

    def put_headers(self, h, data_lenght):
        h.putheader("Content-type", "application/json")
        h.putheader("Content-length", data_lenght)
        if self.credentials:
            import base64
            s = ('%s:%s' % self.credentials).encode('utf-8')
            s = 'Basic ' + base64.b64encode(s).strip().decode('ascii')
            h.putheader('Authorization', s)
        h.endheaders()
        return h

    def emit(self, record):
        """
        Emit a record.

        Send the record to the Web server as a json
        """
        try:
            import http.client
            host = "{}:{}".format(self.host, self.port)
            if self.secure:
                h = http.client.HTTPSConnection(host, context=self.context)
            else:
                h = http.client.HTTPConnection(host)
            url = self.url
            h.putrequest(self.method, url)
            # support multiple hosts on one IP address...
            # need to strip optional :port from host, if present
            i = host.find(":")
            if i >= 0:
                host = host[:i]
            # See issue #30904: putrequest call above already adds this header
            # on Python 3.x.
            # h.putheader("Host", host)
            data = self.mapLogRecord(record)
            data = self.convert_json_to_bytes(data)
            data_lenght = str(len(data))
            h = self.put_headers(h, data_lenght)
            h.send(data)
            h.getresponse()    #can't do anything with the result
        except Exception:
            self.handleError(record)
from logging import Handler
import json
import sys
from logstash import formatter
import http.client

class HTTPLogstashHandler(Handler):
    """
    A class which sends records to a Web server, using POST semantics.
    """
    def __init__(self, host, port, url, secure=False, credentials=None,
                 context=None, tags=None, message_type='logstash', fqdn=False, version=0, level='NOTSET'):
        super(HTTPLogstashHandler, self).__init__(level)
        if not secure and context is not None:
            raise ValueError("context parameter only makes sense with secure=True")
        if version == 1:
            self.formatter = formatter.LogstashFormatterVersion1(message_type, tags, fqdn)
        else:
            self.formatter = formatter.LogstashFormatterVersion0(message_type, tags, fqdn)
        self.tags = tags
        self.port = port
        self.host = host
        self.url = url
        self.method = 'POST'
        self.secure = secure
        self.credentials = credentials
        self.context = context

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
        Send the record to the Web server as a json
        """
        try:
            host = "{}:{}".format(self.host, self.port)
            if self.secure:
                h = http.client.HTTPSConnection(host, context=self.context)
            else:
                h = http.client.HTTPConnection(host)

            data = self.formatter.format(record)
            data_lenght = str(len(data))

            h.putrequest(self.method, self.url)
            h = self.put_headers(h, data_lenght)
            h.send(data)
            h.getresponse()    #can't do anything with the result
        except Exception:
            self.handleError(record)

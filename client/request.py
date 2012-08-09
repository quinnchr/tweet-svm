import urllib2
import json
from urllib import urlencode


class RequestMethod(urllib2.Request):

	def __init__(self, method, *args, **kwargs):
		self._method = method
		urllib2.Request.__init__(self, *args, **kwargs)

	def get_method(self):
		return self._method


class Request:

	def __init__(self, host, auth):
		self.host = host
		self.auth = auth

	def get(self, path):
		auth = self.auth.digest(path)
		request = RequestMethod('GET', self.host + path)
		return self.send_request(request, auth)

	def post(self, path, data):
		auth = self.auth.digest(path, data)
		request = RequestMethod('POST', self.host + path, urlencode(data))
		return self.send_request(request, auth)

	def delete(self, path):
		auth = self.auth.digest(path)
		request = RequestMethod('DELETE', self.host + path)
		return self.send_request(request, auth)

	def send_request(self, request, header):
		request.add_header('Authorization', header)
		try:
			result = urllib2.urlopen(request).read()
		except urllib2.HTTPError, e:
			result = e.fp.read()
		if result:
			data = json.loads(result)
			if 'error' in data:
				raise Exception(data['error'])
				return False
			else:
				return data
		else:
			return True

from auth import Auth
from request import Request


class Connection:

	def __init__(self, host, public_key, private_key):
		self.host = host
		self.public_key = public_key
		self.private_key = private_key
		self.auth = Auth(public_key, private_key)
		self.request = Request(self.host, self.auth)

	def add_user(self):
		return self.request.post('/users/', {})

	def delete_user(self, user):
		return self.request.delete('/users/' + user)

	def get_streams(self):
		return self.request.get('/streams/')

	def add_stream(self, stream):
		return self.request.post('/streams/', {'stream': stream})

	def delete_stream(self, stream):
		return self.request.delete('/streams/' + stream + '/')

	def get_sources(self, stream):
		return self.request.get('/streams/' + stream + '/')

	def add_source(self, stream, source):
		return self.request.post('/streams/' + stream + '/', {'source': source})

	def delete_source(self, stream, source):
		return self.request.delete('/streams/' + stream + '/' + source + '/')

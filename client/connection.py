import urllib
import Auth


class Connection:

	def __init__(self, host, public_key, private_key):
		self.host = host
		self.public_key = public_key
		self.private_key = private_key
		self.auth = Auth(public_key, private_key)

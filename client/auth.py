import hmac
import hashlib
import base64


class Auth:

	def __init__(self, public_key, private_key):
		self.public_key = public_key
		self.private_key = private_key.encode('ascii')

	def digest(self, request, data={}):
		request_args = []
		request_args += [k + '=' + v for k, v in data.iteritems() if k not in ('key', 'digest')]
		request_args.append(request)
		message = '|'.join(request_args)
		return self.public_key + ':' + base64.b64encode(hmac.new(self.private_key, message, hashlib.sha256).digest())

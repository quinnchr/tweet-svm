import xmlrpclib
import subprocess
import redis
import json
import inspect


class CommandError(Exception):

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class Manager:

	def __init__(self, db):
		self.functions = dict(inspect.getmembers(self, predicate=inspect.ismethod))
		self.host = 'http://quinnchr:password@localhost:9001'
		self.twiddler = xmlrpclib.ServerProxy(self.host).twiddler
		self.supervisor = xmlrpclib.ServerProxy(self.host).supervisor
		self.server_key = "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"
		self.db = db

	def dispatch(self, data):
		try:
			data = json.loads(data)
			command = data[u'command']
			options = data[u'options']
			if command in self.functions:
				code = self.functions[command](**options)
		except KeyError, ValueError:
			# bad command, skip it
			pass

	def add_user(self, **kwargs):
		user = uuid.uuid4()
		public_key = base64.b64encode(hmac.new(self.server_key, user, hashlib.sha256).digest())
		private_key = base64.b64encode(hmac.new(self.server_key, random.getrandbits(256), hashlib.sha256).digest())
		self.db.sadd("server:users", user)
		self.db.hset("server:uuids", public_key, user)
		self.db.hset("server:credentials", public_key, private_key)
		return subprocess.call(['useradd', '-r', '-s', '/bin/false', user])

	def add_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		if check_resouce(user, stream):
			raise CommandError('Resource already exists.')
		self.db.sadd(user, stream)
		try:
			self.twiddler.addProgramToGroup(
				'users',
				user + ':' + stream,
				{'command': '/usr/bin/python analyze/analyze.py ' + user + ' ' + stream})
		except xmlrpclib.Fault:
			print "Error adding program"

	def add_source(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		source = kwargs[u'source']
		if check_resouce(user, stream, source):
			raise CommandError('Resource already exists.')
		self.db.sadd(user + ':' + stream, source)
		command = {'action': 'add', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands', json.dumps(command))

	def remove_user(self, **kwargs):
		user = kwargs[u'user']
		if not check_resouce(user):
			raise CommandError('Resource does not exist.')
		code = subprocess.call(['deluser', user])
		code = subprocess.call(['delgroup', user])
		for stream in self.db.smembers(user):
			self.remove_stream(user=user, stream=stream)
		self.db.srem("server:users", user)

	def remove_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		if not check_resouce(user, stream):
			raise CommandError('Resource does not exist.')
		try:
			self.supervisor.stopProcess('users:' + user + ':' + stream)
			self.twiddler.removeProcessFromGroup('users', user + ':' + stream)
		except xmlrpclib.Fault:
			print "Bad process"

		self.db.srem(user, stream)
		for source in self.db.smembers(user + ':' + stream):
			self.remove_source(user=user, stream=stream, source=source)

	def remove_source(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		source = kwargs[u'source']
		if not check_resouce(user, stream, source):
			raise CommandError('Resource does not exist.')
		command = {
			'action': 'remove',
			'user': user,
			'stream': stream,
			'source': source
		}
		self.db.publish('server:commands', json.dumps(command))
		self.db.srem(user + ':' + stream, source)

	def check_resource(user="", stream="", source=""):
		if user:
			resource_pool = "server:users"
			resource = user
		if stream:
			resource_pool = stream
			resource = stream
		if source:
			resource_pool = ":".join((user, stream))
			resouce = source
		return db.smembers(resource_pool, resource)

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = Manager(redis.StrictRedis(host='localhost', port=6379, db=0))
	for command in db.listen():
		controller.dispatch(command['data'])

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
		self.db = db

	def dispatch(self, data):
		try:
			command = data[u'command']
			options = data[u'options']
			if command in self.functions:
				code = self.functions[command](**options)
		except KeyError, ValueError:
			# bad command, skip it
			pass

	def add_user(self, **kwargs):
		user = kwargs[u'user']
		self.db.sadd('server:users', user)
		return subprocess.call(['useradd', '-r', '-s', '/bin/false', user])

	def add_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		self.check_resource(user)
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
		self.check_resource(user, stream)
		self.db.sadd(user + ':' + stream, source)
		command = {'action': 'add', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands', json.dumps(command))

	def remove_user(self, **kwargs):
		user = kwargs[u'user']
		self.check_resource(user)
		code = subprocess.call(['deluser', user])
		code = subprocess.call(['delgroup', user])
		for stream in self.db.smembers(user):
			self.remove_stream(user=user, stream=stream)
		self.db.srem('server:users', user)

	def remove_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		self.check_resource(user, stream)
		try:
			self.supervisor.stopProcess('users:' + user + ':' + stream)
			self.twiddler.removeProcessFromGroup('users', user + ':' + stream)
		except xmlrpclib.Fault:
			print "Bad process"

		for source in self.db.smembers(user + ':' + stream):
			self.remove_source(user=user, stream=stream, source=source)

		self.db.srem(user, stream)

	def remove_source(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		source = kwargs[u'source']
		self.check_resource(user, stream, source)
		command = {
			'action': 'remove',
			'user': user,
			'stream': stream,
			'source': source
		}
		self.db.publish('server:commands', json.dumps(command))
		self.db.srem(user + ':' + stream, source)

	def get_users(self, **kwargs):
		users = []
		for user in self.db.smembers('server:users'):
			users.append(user)
		return users

	def get_streams(self, **kwargs):
		user = kwargs[u'user']
		self.check_resource(user)
		streams = []
		for stream in self.db.smembers(user):
			streams.append(stream)
		return streams

	def get_sources(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		self.check_resource(user, stream)
		sources = []
		for source in self.db.smembers(user + ':' + stream):
			sources.append(source)
		return sources

	def check_resource(self, user, stream="", source=""):
		if not self.db.sismember('server:users', user):
			raise CommandError('User does not exist')
		if stream and not self.db.sismember(user, stream):
			raise CommandError('Stream does not exist')
		if source and not self.db.sismember(user + ':' + stream, source):
			raise CommandError('Source does not exist')

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = Manager(redis.StrictRedis(host='localhost', port=6379, db=0))
	for command in db.listen():
		controller.dispatch(json.loads(command['data']))

import inspect
import json
import redis
import subprocess
import xmlrpclib


class CommandError(Exception):

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


class Manager:

	def __init__(self, db):
		self.functions = dict(inspect.getmembers(self, predicate=inspect.ismethod))
		self.twiddler = xmlrpclib.ServerProxy('http://quinnchr:password@localhost:9001').twiddler
		self.supervisor = xmlrpclib.ServerProxy('http://quinnchr:password@localhost:9001').supervisor
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
		user = kwargs[u'user']
		return subprocess.call(['useradd', '-r', '-s', '/bin/false', user])

	def add_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		self.db.sadd(user, stream)
		try:
			self.twiddler.addProgramToGroup('users', user+':'+stream, {'command':'/usr/bin/python analyze/analyze.py ' + user + ' ' + stream}) 
		except xmlrpclib.Fault:
			print "Error adding program"

	def add_source(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		source = kwargs[u'source']
		self.db.sadd(user + ':' + stream, source)
		command = {'action': 'add', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands', json.dumps(command))

	def remove_user(self, **kwargs):
		user = kwargs[u'user']
		code = subprocess.call(['deluser', user])
		code = subprocess.call(['delgroup', user])
		for stream in self.db.smembers(user):
			self.remove_stream(user=user, stream=stream)

	def remove_stream(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
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
		command = {'action': 'remove', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands', json.dumps(command))
		self.db.srem(user + ':' + stream, source)

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = Manager(redis.StrictRedis(host='localhost', port=6379, db=0))
	for command in db.listen():
		controller.dispatch(command['data'])

import redis
import json
import inspect
import subprocess
import xmlrpclib
import supervisor_twiddler

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
		return subprocess.call(['useradd','-r', '-s', '/bin/false', user])

	def add_stream(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']
		self.twiddler.addProgramToGroup('users', user+':'+stream, {'command':'/usr/bin/python analyze/analyze.py ' + user + ' ' + stream}) 

	def add_source(self, **kwargs):
		user = kwargs[u'user']
		stream = kwargs[u'stream']
		source = kwargs[u'source']
		command = {'action': 'add', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands',json.dumps(command))

	def remove_user(self, **kwargs):
		user = kwargs[u'user']
		code = subprocess.call(['deluser', user])
		return subprocess.call(['delgroup',user])

	def remove_stream(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']
		self.supervisor.stopProcess('users:' + user + ':' + stream)
		self.twiddler.removeProcessFromGroup('users', user + ':' + stream)

	def remove_source(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']
		source  = kwargs[u'source']
		command = {'action': 'remove', 'user': user, 'stream': stream, 'source': source}
		self.db.publish('server:commands',json.dumps(command))

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = Manager(redis.StrictRedis(host='localhost', port=6379, db=0))
	for command in db.listen():
		controller.dispatch(command['data'])

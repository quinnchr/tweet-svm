import redis
import json
import inspect
import subprocess

class CommandError(Exception):

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

class Manager:
	
	def __init__(self):
		self.functions = dict(inspect.getmembers(self, predicate=inspect.ismethod))

	def dispatch(self, data):
		try:
			data = json.loads(data)
			command = data[u'command']
			options = data[u'options']
			if command in self.functions:
				code = self.functions[command](**options)
				if code != 0:
					raise CommandError(code)
		except KeyError, ValueError:
			# bad command, skip it
			pass

	def add_user(self, **kwargs):
		user = kwargs[u'user']
		return subprocess.call(['useradd','-r', '-s', '/bin/false', user])

	def add_stream(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']

	def add_source(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']
		source  = kwargs[u'source']

	def remove_user(self, **kwargs):
		user = kwargs[u'user']
		code = subprocess.call(['deluser', user])
		return subprocess.call(['delgroup',user])

	def remove_stream(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']

	def remove_source(self, **kwargs):
		user = kwargs[u'user']
		stream  = kwargs[u'stream']
		source  = kwargs[u'source']

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = Manager()
	for command in db.listen():
		controller.dispatch(command['data'])

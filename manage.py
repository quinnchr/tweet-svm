import redis
import json
import time
import inspect
import subprocess

class manager:
	
	def __init__(self):
		self.functions = dict(inspect.getmembers(self, predicate=inspect.ismethod))

	def dispatch(self, data):
		try:
			data = json.loads(data)
			command = data[u'command']
			options = data[u'options']
			if command in self.functions:
				print self.functions[command]
				self.functions[command](**options)
		except KeyError, ValueError:
			# bad command, skip it
			pass

	def add_user(self, **kwargs):
		user = kwargs[u'user]
		

	def add_stream(self, **kwargs):
		print kwargs

	def add_source(self, **kwargs):
		print kwargs

	def remove_user(self, **kwargs):
		print kwargs

	def remove_stream(self, **kwargs):
		print kwargs

	def remove_source(self, **kwargs):
		print kwargs

if __name__ == '__main__':
	db = redis.StrictRedis(host='localhost', port=6379, db=0).pubsub()
	db.subscribe('manage')
	# start the main loop
	controller = manager()
	for command in db.listen():
		controller.dispatch(command['data'])

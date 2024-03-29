import json
import numpy
import random
import redis
import sys
import time
from collections import *
from extract import extract
from pymongo import Connection

class Analyze:

	def __init__(self, db, analytics, user, stream):
		self.user = sys.argv[1]
		self.stream = sys.argv[2]
		self.prefix = ':'.join([user, stream])
		self.analytics = analytics
		self.db = db
		self.window = 50
		self.count = {}
		self.rate = {}
		self.get_count()
	

	def process_tick(self):
		while(True):
			stat_stream = defaultdict(dict)
			stat_stream = {'stream': self.stream}
			stats = {}
			self.get_count()
			for source in self.get_sources():
				stat = stat_stream
				stat['source'] = source
				stat['time'] = time.time()
				stat['sample'] = random.uniform(0,1)
				stat['data'] = {}
				prefix = self.prefix + ':' + source
				for key in ('ids','positive','negative'):
					stat['data'][key] = {
						'val' : self.count[source][key], 
						'rate' : self.get_rate(self.rate[source][key])
					}
				self.analytics.insert(stat)
				del stat['_id']
				stats[source] = stat
			yield stats
			time.sleep(1)

	def get_count(self):
		for source in self.get_sources():
			if source not in self.count:
				self.count[source] = {}
				self.rate[source] = {}
			for key in ('ids','positive','negative'):
				prefix = self.prefix + ':' + source + ':' + key
				count = self.db.zcard(prefix)
				if key not in self.rate[source]:
					self.rate[source][key] = []
				try:
					self.rate[source][key].append(count - self.count[source][key])
				except KeyError:
					self.rate[source][key].append(0)
				self.count[source][key] = count
				if len(self.rate[source][key]) > self.window:
					self.rate[source][key] = self.rate[source][key][-50:]
				else:
					self.rate[source][key] = [0]*(self.window - len(self.rate[source][key])) + self.rate[source][key]
			

	def get_rate(self,x):
		# exponential smoothing, like a rolling average but we weight older values less
		return self.smooth(numpy.array(x))[len(x)]
	
	def get_sources(self):
		return db.smembers(self.prefix)

	def smooth(self,x, window_len=10, window='hanning'):

		if x.ndim != 1:
			raise ValueError, "Smooth only accepts 1 dimension arrays."

		if x.size < window_len:
			raise ValueError, "Input vector needs to be bigger than window size."

		if window_len<3:
			return x

		if not window in ['flat', 'hanning', 'hamming', 'bartlett', 'blackman']:
			raise ValueError, "Window is one of 'flat', 'hanning', 'hamming', 'bartlett', 'blackman'"


		s=numpy.r_[x[window_len-1:0:-1],x,x[-1:-window_len:-1]]
		if window == 'flat': #moving average
			w=numpy.ones(window_len,'d')
		else:
			w=eval('numpy.'+window+'(window_len)')

		y=numpy.convolve(w/w.sum(),s,mode='valid')
		return y

if __name__ == "__main__":
	mongo = Connection('localhost', 27017).ml[sys.argv[1]].analytics
	db = redis.StrictRedis(host='localhost', port=6379, db=0)
	analytics = Analyze(db,mongo,sys.argv[1],sys.argv[2])
	for stat in analytics.process_tick():
		db.publish('server:emit',json.dumps(stat))
		print stat
		sys.stdout.flush()



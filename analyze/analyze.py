import redis
import json
import time
import numpy
from pymongo import Connection

def read_queue(db, analytics):
	keyword = True
	while(keyword):
		keyword = db.brpop(queue)[1]
		series = window(db, keyword, 50)

		stats = {
			'total' : {
				'val' : db.zcard('ids:'+keyword), 
				'rate' : rate(series['ids'])
			}, 
			'positive' : {
				'val' : db.zcard('positive:'+keyword), 
				'rate' : rate(series['positive'])
			}, 
			'negative' : {
				'val' : db.zcard('negative:'+keyword), 
				'rate' : rate(series['negative'])
			},
			'time' : time.time()
		}
		yield keyword, stats
		analytics.insert(stats)

def rate(x):
	period = numpy.diff(x)
	frequency = numpy.divide(1,period)
	# exponential smoothing, like a rolling average but we weight older values less
	return smooth(frequency)[len(x)]

def window(db, keyword, length):
	keys = ['positive', 'negative', 'ids']
	count = lambda x : db.zcard(x+':'+keyword)
	tweets = lambda x : map(lambda y : float(y[1])/(10**6), db.zrange(x+':'+keyword, count(x) - length, count(x), withscores = True))
	series = {}
	for i in keys:
		series[i] = tweets(i) + [time.time()]
	return series

def smooth(x, window_len=10, window='hanning'):

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

mongo = Connection('localhost', 27017).twitter.analytics
db = redis.StrictRedis(host='localhost', port=6379, db=0)
queue = 'analyze:queue'
sentiment = None
old_sentiment = None
ratio = []

for keyword, stat in read_queue(db,mongo):
	# find intervals for feature extraction
	if stat['positive']['rate'] - stat['negative']['rate'] < 0:
		sentiment = 'negative'
		num_key, den_key = 'negative', 'positive'
	else:
		sentiment = 'positive'
		num_key, den_key = 'positive', 'negative'

	if sentiment == old_sentiment:
		ratio.append(stat[num_key]['rate']/stat[den_key]['rate'])
		score = len(ratio) * numpy.average(ratio)
		stop = stat['time']
	elif len(ratio) > 0:
		db.publish('extraction:'+keyword, json.dumps({'score' : score, 'interval' : (start,stop)}))
		print str(score) + ': ' + str(start) + ' ' + str(stop)
		start = stat['time']
		ratio = []
	else:
		start = stat['time']

	old_sentiment = sentiment
	# TODO: sandboxed python for custom analytics
	# add final statistics here
	stat['sentiment'] = sentiment
	db.publish('analytics:'+keyword, json.dumps(stat))



import json
import redis
import sys
import time
from extract import extract


class cluster:

	def __init__(self, user, stream, source, sentiment, length, rate):
		self.extract_rate = rate
		self.info = extract(user, stream, source, sentiment, length)
		self.ticker = 0

	def process_tick(self):
		while(True):
			if self.ticker % self.extract_rate == 0:
				self.info.update()
				yield {'groups': self.info.groups}
			time.sleep(1)
			self.ticker += 1

if __name__ == "__main__":
	db = redis.StrictRedis(host='localhost', port=6379, db=0)
	groups = cluster(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]))
	for data in groups.process_tick():
		db.publish('server:emit', json.dumps(data))
		print data


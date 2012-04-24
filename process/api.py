import tornado.ioloop
import tornado.web
import json, classify, redis, time, hashlib

class MainHandler(tornado.web.RequestHandler):

	def prepare(self):
		remaining = self.limit(self.request.remote_ip)
		if remaining <= 0:
			self.set_status(420)
			self.write(json.dumps({'error' : 'rate limit'}))

	def error(self):
		raise tornado.web.HTTPError(400)

	def get(self):
		self.error()

	def post(self):
		text = self.get_argument('text')
		user = self.request.remote_ip
		user_sentiment = self.get_argument('sentiment', False)
		remaining = self.limit(user)
		sentiment_key = {0: 'negative', 2: 'neutral', 4: 'positive'}
		if text != '':	
			if user_sentiment in ('positive', 'negative', 'neutral'):
				self.learn(user, text, user_sentiment)
				output = json.dumps({'rate-limit-remaining' : self.limit(user)})
			elif user_sentiment == False:
				score = svm.classify(text)
				sentiment = {'sentiment' : sentiment_key[score]}
				db.zadd('requests:'+user, time.time(), time.time())
				self.limit(user)
				output = json.dumps(sentiment)
			else:
				self.error()
		self.write(output)

	def learn(self, user, text, sentiment):
		md5 = hashlib.md5()
		md5.update(text)
		hash_key = md5.hexdigest()
		db.hset('api:'+sentiment, hash_key, text)
		db.zadd('api:'+user, time.time(), hash_key)
	
	def limit(self, user):
		current_time = time.time()
		requests = len(db.zrangebyscore('requests:'+user, current_time - 3600, current_time))
		contributions = len(db.zrangebyscore('api:'+user, current_time - 3600, current_time))
		remaining = min((100 + 10*contributions) - requests, 1000)

		self.set_header('X-Ratelimit-Limit', 100 + 10*contributions)
		self.set_header('X-Ratelimit-Remaining', remaining)

		return remaining

application = tornado.web.Application([
	(r"/", MainHandler),
])

if __name__ == "__main__":
	print 'Initializing Support Vector Machine...'
	svm = classify.SVM('data/t2-samples.npy','data/t2-classes.npy','data/t2-vocabulary.npy')
	print 'SVM Initialized'
	db = redis.StrictRedis(host='localhost', port=6379, db=0)
	application.listen(8000)
	tornado.ioloop.IOLoop.instance().start()

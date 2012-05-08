import redis
import json
import time
import classify
import pickle
from multiprocessing import Pool

queue = 'process:queue'

def init(obj):
	global svm
	svm = obj

def f(x):
	global svm
	return svm.classify(x)

def read_queue():
	tweet = db.brpop(queue)[1]
	while(tweet):
		tweet = db.brpop(queue)[1]
		yield tweet

print 'Initializing Support Vector Machine...'
svm = pickle.load(open('data/svm-reduced.pickle','r'))
pool = Pool(initializer=init,initargs=(svm,))
def classify(x):
	return pool.apply(f,(x,)) 
print 'SVM Initialized'

db = redis.StrictRedis(host='localhost', port=6379, db=0)
sentiment = {0: 'negative', 2: 'neutral', 4: 'positive'}
sentiment_key = lambda keyword : {0: 'negative:' + keyword, 2: 'neutral:' + keyword, 4: 'positive:' + keyword}

for tweet in read_queue():
	tweet = json.loads(tweet)
	tweet_text = tweet[u'text'].encode('ascii','ignore')
	tweet_id = tweet[u'id']
	#tweet_time = int(time.mktime(time.strptime(tweet[u'created_at'],'%a %b %d %H:%M:%S +0000 %Y')) * 1000)
	tweet_time = time.time() * 10**6
	keyword = tweet[u'keyword']
	tweets = 'tweets:' + keyword
	ids = 'ids:' + keyword
	score = classify(tweet_text)
	print 'Classified: ' + sentiment[score]
	tweet[u'sentiment'] = sentiment[score]
	db.hset(tweets,tweet_id,json.dumps(tweet))
	db.zadd(ids, tweet_time, tweet_id)
	db.zadd(sentiment_key(keyword)[score], tweet_time, tweet_id)
	db.publish(keyword,tweet_id)
	db.lpush('analyze:queue', keyword)



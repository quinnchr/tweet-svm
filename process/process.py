import redis, sys, json, time, classify

if(len(sys.argv) != 2):
	print 'Process takes exactly one argument'
	sys.exit()
else:
	keyword = sys.argv[1]
	queue = 'queue:' + keyword
	tweets = 'tweets:' + keyword
	ids = 'ids:' + keyword
	print 'Processing ' + keyword
	svm = classify.SVM('data/training-samples.npy','data/training-classes.npy','data/training-vocabulary.npy')

db = redis.StrictRedis(host='localhost', port=6379, db=0)
sentiment = {0: 'negative', 2: 'neutral', 4: 'positive'}
sentiment_key = {0: keyword + ':negative', 2: keyword + ':neutral', 4: keyword + ':positive'}

while(True):
	tweet = db.brpop(queue)[1]
	tweet = json.loads(tweet)
	tweet_text = tweet[u'text'].encode('ascii','ignore')
	tweet_id = tweet[u'id']
	tweet_time = int(time.mktime(time.strptime(tweet[u'created_at'],'%a %b %d %H:%M:%S +0000 %Y')) * 1000)
	score = svm.classify(tweet_text)
	print 'Classified: ' + sentiment[score]
	tweet[u'sentiment'] = sentiment[score]
	db.hset(tweets,tweet_id,json.dumps(tweet))
	db.zadd(ids, tweet_time, tweet_id)
	db.zadd(sentiment_key[score], tweet_time, tweet_id)
	db.publish(keyword,tweet_id)



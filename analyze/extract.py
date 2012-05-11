from time import time
from sklearn.feature_extraction import text
from sklearn import decomposition
from collections import Counter
import redis, sys, json, pickle, numpy, re

n_samples = 5000
n_features = 1000
n_topics = 10
n_top_words = 20

# grab the data for our ids, need to be careful here and put a cap on the hash size
def get_tweet(db,key,i):
	collection, keyword = key.split(':')
	tweet_id = db.zrange(key,i,i)[0]
	tweet = json.loads(db.hget('tweets:'+keyword, tweet_id))
	return tweet

db = redis.StrictRedis(host='localhost', port=6379, db=0)
key = 'positive:' + sys.argv[1]
# let's determine our interval
interval = (float(sys.argv[2])*10**6, float(sys.argv[3])*10**6)
start = interval[0]
stop = interval[1]
# add the intervals to the sorted set then get the rank and delete them to determine the range of our subset
db.zadd(key,start,'START')
db.zadd(key,stop,'STOP')
start_index = db.zrank(key,'START')
stop_index = db.zrank(key,'STOP')
db.zrem(key,'START')
db.zrem(key,'STOP')
# now we take a sampling to reduce our feature space
ids = set(numpy.vectorize(int)(numpy.linspace(start_index,stop_index,num=n_samples)) - 2) # shift to account for deletion of our markers
data = []
tweet_urls = []
url_regex = re.compile(r'([A-Za-z]{3,9})://([-;:&=\+\$,\w]+@{1})?([-A-Za-z0-9\.]+)+:?(\d+)?((/[-\+~%/\.\w]+)?\??([-\+=&;%@\.\w]+)?#?([\w]+)?)?')
for i in ids:
	tweet = get_tweet(db,key,i)
	tweet_text = tweet[u'text'].encode('ascii','ignore')
	# count URLs then scrub them out
	for tweet_url in url_regex.finditer(tweet_text):
		tweet_urls.append(tweet_url.group(0))
		tweet_text = tweet_text.replace(tweet_url.group(0),'')
	# scrub out repeated characters
	tweet_text = re.sub(r'(\w)\1{2,}','',tweet_text)
	# scrub out mentions
	tweet_text = re.sub(r'(@\w+)','', tweet_text)
	if re.match(r'(RT | RT| RT )',tweet_text) == None:
		data.append(tweet_text)

print '\n'.join(tweet_urls)
tweet_urls = Counter(tweet_urls)
#print tweet_urls.most_common(10)


vectorizer = text.CountVectorizer(max_df=0.95, max_features=n_features, stop_words='english', max_n=3)
counts = vectorizer.fit_transform(data)
tfidf = text.TfidfTransformer().fit_transform(counts)

# Fit the NMF model
#print "Fitting the NMF model on with n_samples=%d and n_features=%d..." % (n_samples, n_features)
nmf = decomposition.NMF(n_components=n_topics).fit(tfidf)

# Inverse the vectorizer vocabulary
feature_names = vectorizer.get_feature_names()

for topic_idx, topic in enumerate(nmf.components_):
	print "Topic #%d:" % topic_idx
	print " ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]])

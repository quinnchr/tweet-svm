from time import time
from sklearn.feature_extraction import text
from sklearn import decomposition
from collections import Counter
from pymongo import Connection
import redis, sys, json, pickle, numpy, re

n_samples = 5000
n_features = 1000
n_topics = 10
n_top_words = 20

mongo = Connection('localhost', 27017).ml
# let's determine our interval
user, stream, source, sentiment, start, stop = sys.argv[1:]
db = mongo[user].data
interval = (float(start)*10**3, float(stop)*10**3)
start = interval[0]
stop = interval[1]
data = []
tweet_urls = []
url_regex = re.compile(r'([A-Za-z]{3,9})://([-;:&=\+\$,\w]+@{1})?([-A-Za-z0-9\.]+)+:?(\d+)?((/[-\+~%/\.\w]+)?\??([-\+=&;%@\.\w]+)?#?([\w]+)?)?')

query = {'user': user, 'stream': stream, 'source': source, 'sentiment': sentiment, 'time': {'$gte': start, '$lte': stop}}

for tweet in db.find(query):
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

#print '\n'.join(tweet_urls)
tweet_urls = Counter(tweet_urls)
print tweet_urls.most_common(10)


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

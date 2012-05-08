from time import time
from sklearn.feature_extraction import text
from sklearn import decomposition
import redis, sys, json, pickle, numpy, re

n_samples = 1000
n_features = 1000
n_topics = 10
n_top_words = 20

db = redis.StrictRedis(host='localhost', port=6379, db=0)
keyword = sys.argv[1]
interval = (float(sys.argv[2])*10**6, float(sys.argv[3])*10**6)
ids = db.zrangebyscore('negative:'+keyword,interval[0],interval[1])
data = []
for i in ids:
	tweet = json.loads(db.hget('tweets:'+keyword, i))
	tweet_text = tweet[u'text'].encode('ascii','ignore')
	tweet_text = re.sub(r'([A-Za-z]{3,9})://([-;:&=\+\$,\w]+@{1})?([-A-Za-z0-9\.]+)+:?(\d+)?((/[-\+~%/\.\w]+)?\??([-\+=&;%@\.\w]+)?#?([\w]+)?)?','',tweet_text)
	tweet_text = re.sub(r'(\w)\1{2,}','',tweet_text)
	tweet_text = re.sub(r'(@\w+)','', tweet_text)
	if re.match(r'(RT | RT| RT )',tweet_text) == None:
		data.append(tweet_text)

vectorizer = text.CountVectorizer(max_df=0.95, max_features=n_features, stop_words='english', max_n=3)
counts = vectorizer.fit_transform(data)
tfidf = text.TfidfTransformer().fit_transform(counts)

# Fit the NMF model
print "Fitting the NMF model on with n_samples=%d and n_features=%d..." % (
    n_samples, n_features)
nmf = decomposition.NMF(n_components=n_topics).fit(tfidf)

# Inverse the vectorizer vocabulary to be able
feature_names = vectorizer.get_feature_names()

for topic_idx, topic in enumerate(nmf.components_):
    print "Topic #%d:" % topic_idx
    print " ".join([feature_names[i]
                    for i in topic.argsort()[:-n_top_words - 1:-1]])
    print

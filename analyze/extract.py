from sklearn.feature_extraction import text
from collections import defaultdict
from sklearn import decomposition
from sklearn.cluster import Ward
from collections import Counter
from pymongo import Connection
import re
import time
import operator

class extract:

	def __init__(self, user, stream, source, sentiment, duration):
		self.samples = 5000
		self.features = 1000
		self.topics = 10
		self.top_words = 20
		self.duration = duration
		self.mongo = Connection('localhost', 27017).ml
		# let's determine our interval
		self.db = self.mongo[user].data
		self.stop = (time.time() - int(self.duration)) * 1000
		self.data = []
		self.urls = []
		self.url_regex = re.compile(r'([A-Za-z]{3,9})://([-;:&=\+\$,\w]+@{1})?([-A-Za-z0-9\.]+)+:?(\d+)?((/[-\+~%/\.\w]+)?\??([-\+=&;%@\.\w]+)?#?([\w]+)?)?')
		self.query = {'user': user, 'stream': stream, 'source': source, 'sentiment': sentiment, 'time': {'$gte': self.stop}}
		self.update()

	def update(self):
		tweet_urls = []
		data = []
		final = []
		self.stop = (time.time() - int(self.duration)) * 1000
		self.query['time']['$gte'] = self.stop
		for tweet in self.db.find(self.query):
			tweet_text = tweet[u'text'].encode('ascii', 'ignore')
			original = tweet_text
			# count URLs then scrub them out
			for tweet_url in self.url_regex.finditer(tweet_text):
				tweet_urls.append(tweet_url.group(0))
				tweet_text = tweet_text.replace(tweet_url.group(0), '')
			# scrub out repeated characters
			tweet_text = re.sub(r'(\w)\1{2,}', '', tweet_text)
			# scrub out mentions
			tweet_text = re.sub(r'(@\w+)', '', tweet_text)
			if re.match(r'(RT | RT| RT )', tweet_text) == None:
				if tweet_text not in data:
					data.append(tweet_text)
					final.append({'tweet': original, 'score': tweet[u'data'][u'user'][u'followers_count'] * (1 + tweet[u'data'][u'retweet_count'])})
		tweet_urls = Counter(tweet_urls)
		self.data = data
		self.urls = tweet_urls
		self.vectorizer = text.CountVectorizer(max_df=0.95, max_features=self.features, stop_words='english', max_n=2)

		counts = self.vectorizer.fit_transform(data)
		self.tfidf = text.TfidfTransformer().fit_transform(counts)
		ward = Ward(n_clusters=self.topics).fit(self.tfidf.todense())
		self.cluster = defaultdict(list)
		for index, label in enumerate(ward.labels_):
			self.cluster[label].append(final[index])
		self.groups = []
		for i, cluster in self.cluster.iteritems():
			group = {}
			group['cluster'] = sorted(cluster, key=operator.itemgetter('score'))
			max_key = max(cluster, key=operator.itemgetter('score'))
			group['topic'] = max_key['tweet']
			self.groups.append(group)

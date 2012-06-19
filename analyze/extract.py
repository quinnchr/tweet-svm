from sklearn.feature_extraction import text
from sklearn import decomposition
from collections import Counter
from pymongo import Connection
import re
import time


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
		self.stop = (time.time() - int(self.duration)) * 1000
		self.query['time']['$gte'] = self.stop
		for tweet in self.db.find(self.query):
			tweet_text = tweet[u'text'].encode('ascii', 'ignore')
			# count URLs then scrub them out
			for tweet_url in self.url_regex.finditer(tweet_text):
				tweet_urls.append(tweet_url.group(0))
				tweet_text = tweet_text.replace(tweet_url.group(0), '')
			# scrub out repeated characters
			tweet_text = re.sub(r'(\w)\1{2,}', '', tweet_text)
			# scrub out mentions
			tweet_text = re.sub(r'(@\w+)', '', tweet_text)
			if re.match(r'(RT | RT| RT )', tweet_text) == None:
				data.append(tweet_text)
		tweet_urls = Counter(tweet_urls)
		self.data = data
		self.urls = tweet_urls
		self.vectorizer = text.CountVectorizer(max_df=0.95, max_features=self.features, stop_words='english', max_n=2)

		counts = self.vectorizer.fit_transform(data)
		tfidf = text.TfidfTransformer().fit_transform(counts)
		# Fit the NMF model
		#print "Fitting the NMF model on with n_samples=%d and n_features=%d..." % (n_samples, n_features)
		self.nmf = decomposition.NMF(n_components=self.topics).fit(tfidf)
		# Inverse the vectorizer vocabulary
		feature_names = self.vectorizer.get_feature_names()
		self.features = []
		for topic_idx, topic in enumerate(self.nmf.components_):
			self.features.append([feature_names[i] for i in topic.argsort()[:-self.top_words - 1:-1]])

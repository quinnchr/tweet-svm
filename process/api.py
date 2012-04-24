import tornado.ioloop
import tornado.web
import json, classify

class MainHandler(tornado.web.RequestHandler):

	def error(self):
		raise tornado.web.HTTPError(400)

	def get(self):
		self.error()

	def post(self):
		text = self.get_argument('text')
		sentiment_key = {0: 'negative', 2: 'neutral', 4: 'positive'}
		if text != '':
			score = svm.classify(text)
			sentiment = {'sentiment' : sentiment_key[score]}
			self.write(json.dumps(sentiment))
		else:
			self.error()

application = tornado.web.Application([
	(r"/", MainHandler),
])

if __name__ == "__main__":
	print 'Initializing Support Vector Machine...'
	svm = classify.SVM('data/t2-samples.npy','data/t2-classes.npy','data/t2-vocabulary.npy')
	print 'SVM Initialized'
	application.listen(8000)
	tornado.ioloop.IOLoop.instance().start()

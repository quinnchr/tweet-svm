import redis, sys, json, time, classify

if(len(sys.argv) != 2):
	print 'Process takes exactly one argument'
	sys.exit()
else:
	text = sys.argv[1]
	svm = classify.SVM('/home/quinn/Documents/tweet-svm/process/data/training-samples.npy','/home/quinn/Documents/tweet-svm/process/data/training-classes.npy','/home/quinn/Documents/tweet-svm/process/data/training-vocabulary.npy')

sentiment = {0: 'negative', 2: 'neutral', 4: 'positive'}
score = svm.classify(text)

print json.dumps({'sentiment' : sentiment[score]})


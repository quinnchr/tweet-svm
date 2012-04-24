var redis = require("redis"),
	db = redis.createClient(),
	client = redis.createClient();

var io = require('socket.io');
var express = require('express');

var app = express.createServer()
  , io = io.listen(app);

var arguments = process.argv.splice(2);
var keyword = arguments[0];
var tweets = 'tweets:' + keyword;
var count = {'negative': 0, 'positive' : 0, 'neutral' : 0, 'total' : 0}

app.listen(8080);

io.sockets.on('connection', function (socket) {

	client.subscribe(keyword);

	client.on("error", function (err) {
		console.log("Error " + err);
	});

	client.on("message", function (channel, id) {
		db.hget(tweets, id, function(err, obj) {
			tweet = JSON.parse(obj);
			count[tweet.sentiment]++;
			socket.emit('tweet',tweet);
		});
	});

});
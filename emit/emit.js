var redis = require("redis")
var io = require('socket.io');
var express = require('express');

var mongo = require('mongodb'),
  Server = mongo.Server,
  Db = mongo.Db;

var app = express.createServer()
  , io = io.listen(app);

app.listen(8080);

io.sockets.on('connection', function (socket) {

	socket.emit('init',{});
	server = new Server('localhost', 27017, {auto_reconnect: true});
	mongo = new Db('ml', server);

	db = redis.createClient();

	db.on("error", function (err) {
		console.log("Error " + err);
	});

	db.on("message", function (channel, message) {
		data = JSON.parse(message);
		socket.emit('data', data);
	});

	db.subscribe('server:emit');

	socket.on('interval', function (message) {
		stop = parseInt(message.stop);
		start = parseInt(message.start);
		length = stop - start;
		mongo.open(function(err, db) {
			if(!err) {
				mongo.collection('quinnchr.analytics', function(err, collection) {
					collection.count(function(err, count) {
						current = parseInt((new Date()).getTime()/1000);
						index = count - (current - start);
						collection.find({},{sort:[['_id',1]],skip:index,limit:length}).toArray(function(err, items) {
							var data = [];
							for(var i = items.length - 1; i > 0; i--) {
								data[i] = items[i].twitter.positive.rate - items[i].twitter.negative.rate;
							}
							socket.emit('interval', data);
							mongo.close();
						});
					});
				});
			};
		});		
	});

});


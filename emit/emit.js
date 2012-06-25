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
		stop = message.stop;
		start = message.start;
		length = stop - start;
		user = message.user.user;
		stream = message.user.stream;
		source = message.user.source;
		mongo.open(function(err, db) {
			if(!err) {
				mongo.collection(user+'.analytics', {safe: true}, function(err, collection) {
					// take a sample
					samples = 3600;
					factor = samples/length;
					query = {'stream': stream, 'source': source, 'time' : {'$gte' : stop - 10*length , '$lte' : stop}};
					console.log(query);
					collection.find(query ,{'sort':[['time',1]]}).toArray(function(err, items) {
						var data = [];
						var net = 0;
						console.log(items.length);
						for(var i = items.length - 1; i > 0; i--) {
							data[i] = items[i].data.positive.rate - items[i].data.negative.rate;
							net += data[i];
						}
						response = {};
						response.graph = data.slice(-length);
						response.navigator = data.slice(-length*10);
						response.net = net;
						socket.emit('interval', response);
						mongo.close();
					});
					
				});
			};
		});		
	});

});


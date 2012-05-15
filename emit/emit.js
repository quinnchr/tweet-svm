var redis = require("redis")
var io = require('socket.io');
var express = require('express');

var app = express.createServer()
  , io = io.listen(app);

app.listen(8080);

io.sockets.on('connection', function (socket) {

	db = redis.createClient();

	db.on("error", function (err) {
		console.log("Error " + err);
	});

	db.on("message", function (channel, message) {
		data = JSON.parse(message);
		socket.emit('data', data);
	});

	db.subscribe('server:emit');

});

twitter = require('./components/api-feeds.js').twitterFeed

var redis = require("redis"),
	db = redis.createClient(),
	command = redis.createClient();

db.on("error", function (err) {
	console.log("Error " + err);
});

command.on("error", function (err) {
	console.log("Error " + err);
});

command.on("message", function (channel, message) {
	cmd = JSON.parse(message);
	switch(cmd.action) {
		case 'add':
			subscriptions.subscribe(cmd.user, cmd.stream, cmd.source, db);
			break;
		case 'remove':
			subscriptions.unsubscribe(cmd.user, cmd.stream, cmd.source);
			break;
	}
});

command.subscribe('server:commands');

subscription = function() {

	this.subscriptions = new Array();

	this.subscribe = function(user, stream, source, db) {
		var twitterClient = new twitter();

		var count = 0;

		twitterClient.init({
			consumer_key : 'wjhm2fFmfWsGBwQcOdnzkQ',
			consumer_secret : '8JZQvIkSx2nVnoq68VbaBTE6NQbPt0PG46gzTdqAwE',
			access_token : '331287658-gtN64eoMdlkBvWAdtysyuw0yrXqEEFi2AedK5Quc',
			access_token_secret : 'BhkW3DGIdZgkHdVISo42Ua8WJkuqgwQWwsOm7B1DEE'
		});

		twitterClient.onResponse(function(response){
			var time = new Date(response.created_at);
			console.log(response);
			if(response.id && response.user.lang == 'en') {
				response.keyword = source;
				data = {'time': time.getTime(), 'text': response.text, 'source': source, 'stream': stream, 'user': user, 'data': response}
				db.lpush('process:queue', JSON.stringify(data));
				count++;
			}
		})

		twitterClient.setMethod('track');
		twitterClient.addKeywords(source);
		twitterClient.server();
		this.subscriptions[user] = this.subscriptions['user'] || [];
		this.subscriptions[user][stream] = this.subscriptions[user][stream] || [];
		this.subscriptions[user][stream][source] = twitterClient.twitter;
	}

	this.unsubscribe = function(user, stream, source) {
		this.subscriptions[user][stream][source].connection.end();
	}

}

subscriptions = new subscription();


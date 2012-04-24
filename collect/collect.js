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
			db.sadd('server:keywords', cmd.keyword);		
			subscriptions.subscribe(cmd.keyword,db);
			break;
		case 'remove':
			db.srem('server:keywords', cmd.keyword);
			subscriptions.unsubscribe(cmd.keyword);
			break;
	}
});

command.subscribe('server:commands');

subscription = function() {

	this.subscriptions = new Array();

	this.subscribe = function(keyword, db) {
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
			if(response.id && response.user.lang == 'en') {
				response.keyword = keyword;
				db.lpush('server:queue', JSON.stringify(response));
				count++;
			}
		})

		twitterClient.setMethod('track');
		twitterClient.addKeywords(keyword);
		twitterClient.server();
		this.subscriptions[keyword] = twitterClient.twitter;
	}

	this.unsubscribe = function(keyword) {
		this.subscriptions[keyword].connection.end();
	}

}

subscriptions = new subscription();

db.smembers('server:keywords', function(err, keywords) {
	keywords.forEach(function(keyword, i) {
		subscriptions.subscribe(keyword,db)
	});
});


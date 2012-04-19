twitter = require('./components/api-feeds.js').twitterFeed
twitter = new twitter();

var redis = require("redis"),
	db = redis.createClient();

db.on("error", function (err) {
	console.log("Error " + err);
});

var arguments = process.argv.splice(2);
var keyword = arguments[0];
var count = 0;

twitter.init({
	consumer_key : 'wjhm2fFmfWsGBwQcOdnzkQ',
	consumer_secret : '8JZQvIkSx2nVnoq68VbaBTE6NQbPt0PG46gzTdqAwE',
	access_token : '331287658-gtN64eoMdlkBvWAdtysyuw0yrXqEEFi2AedK5Quc',
	access_token_secret : 'BhkW3DGIdZgkHdVISo42Ua8WJkuqgwQWwsOm7B1DEE'
});

twitter.onResponse(function(response){
	var time = new Date(response.created_at);
	if(response.id && response.user.lang == 'en') {
		console.log('Collected: ' + count);
		db.lpush('queue:'+keyword, JSON.stringify(response));
		count++;
	}
})

twitter.setMethod('track');
twitter.addKeywords(keyword);
twitter.server();

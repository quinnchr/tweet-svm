var http = require('http');
var exec = require('child_process').exec;
var querystring = require('querystring');

http.createServer(function (req, res) {
	if (req.method == 'POST') {
		
		var body = '';

		req.on('data', function(chunk) {
			body += chunk.toString();
		});

		req.on('end', function() {
			res.writeHead(200, "OK", {'Content-Type': 'text/html'});
			var text = querystring.parse(body)['text'];
			exec("python ../process/api.py '"+text+"'", function (error, stdout, stderr) {
				if (error !== null) {
					console.log('exec error: ' + error);
				}
				res.write(stdout);
				res.end();
			});
		});

	} else {
		res.writeHead(200, "OK", {'Content-Type': 'text/html'});
		res.end('{}');
	}
}).listen(8000, '10.5.3.82');
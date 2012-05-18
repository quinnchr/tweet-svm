function graph(selector, obj, length) {

	this.length = length;
	this.obj = obj;
	this.graph = new area(selector, obj, length);

	this.redraw = function(data) {
		if(typeof data != 'undefined') {
			obj.data = data;
		}
		$(selector + ' > svg').remove();
		this.graph.ticker.stop();
		this.graph = new area(selector, this.obj, this.length);
	}

}

function area(selector, obj, length) {
	this.n = length;
	this.duration = 1000;
	this.now = new Date();
	this.obj = obj;
	this.limit = 3600;
	this.scale = false;

	if(this.n > this.limit) {
		this.duration = this.n/this.limit * 1000;
		this.n = this.limit;
		this.scale = true;
	}
	
	if(typeof this.obj.data == 'undefined') {
		this.obj.data = d3.range(this.n).map(function(){ return 0;});
	} else {
		fill = this.n - this.obj.data.length;
		if(fill > 0) {
			zeroes = d3.range(fill).map(function(){ return 0;});
			this.obj.data = zeroes.concat(this.obj.data);
		} else {
			this.obj.data = this.obj.data.slice(-1*this.n);
		}
	}
	var margin = {top: 10, right: 0, bottom: 20, left: -1},
		width = parseInt(d3.select(selector).style('width')) - margin.left - margin.right,
		height = parseInt(d3.select(selector).style('height')) - margin.top - margin.bottom;

	this.x = d3.time.scale()
		.domain([this.now - this.n*this.duration, this.now])
		.range([0, width]);

	this.y = d3.scale.linear()
		.domain([-5, 5])
		.range([height, 0]);

	this.svg = d3.select(selector).append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	this.clips = this.svg.append("defs");

	this.clips.append("clipPath")
		.attr("id", "positive")
		.append("rect")
		.attr("width", width)
		.attr("height", height/2);

	this.clips.append("clipPath")
		.attr("id", "negative")
		.append("rect")
		.attr("width", width)
		.attr("height", height/2)
		.attr("transform", "translate(0," + height/2 + ")");

	this.xaxis = d3.svg.axis().scale(this.x).orient("bottom")

	this.xAxis = this.svg.append("g")
		.attr("class", "x axis")
		.attr("transform", "translate(0," + height + ")")
		.call(this.xaxis);

	this.yaxis = d3.svg.axis().scale(this.y).orient("left")
	
	this.yAxis = this.svg.append("g")
		.attr("class", "y axis")
		.call(this.yaxis);



	this.svg.append("svg:g")
		.attr("class", "y stripe")
		.attr("transform", "translate(0,0)")
		.call(this.yaxis.tickSubdivide(1).ticks(10).tickSize(-width));

	this.svg.append("svg:g")
		.attr("class", "y grid")
		.attr("transform", "translate(0,0)")
		.call(this.yaxis.tickSubdivide(0).tickValues([0]).tickSize(-width));

	x = this.x;
	y = this.y;
	n = this.n;
	duration = this.duration;
	now = this.now;

	this.area = d3.svg.area()
		.interpolate("basis")
		.x(function(d, i) { return x(now - (n - 1 - i) * duration); })
		.y0(function(d){ return height/2 })
		.y1(function(d, i) { return y(d); });

	this.positive_area = this.svg.append("g")
		.attr("clip-path", "url(#positive)")
		.append("path")
		.data([this.obj.data])
		.attr("class", "positive")
		.attr("d", this.area);

	this.negative_area = this.svg.append("g")
		.attr("clip-path", "url(#negative)")
		.append("path")
		.data([this.obj.data])
		.attr("class", "negative")
		.attr("d", this.area);

	this.ticker = new tick(this);

}

function tick(parent) {

	if(typeof parent.state == 'undefined') {
		parent.state = true;
	}
	
	if(parent.state == true) {
		// push a new data point onto the back
		if(typeof parent.obj.stats != 'undefined') {
			stat = parent.obj.stats.twitter;
			val = stat.positive.rate - stat.negative.rate;
		} else {
			val = 0;
		}
		parent.obj.data.push(val);
		now = new Date();
		parent.x.domain([now - (parent.n - 2) * parent.duration, now]);

		// redraw the line, and slide it to the left

		// slide the x-axis left
		parent.xAxis.transition()
			.duration(parent.duration)
			.ease("linear")
			.call(parent.xaxis);

		parent.negative_area
			.attr("d", parent.area)
			.attr("transform", null)
			.transition()
			.duration(parent.duration)
			.ease("linear")
			.attr("transform", "translate(" + x(now - (parent.n - 1) * parent.duration) + ")");

		parent.positive_area
			.attr("d", parent.area)
			.attr("transform", null)
			.transition()
			.duration(parent.duration)
			.ease("linear")
			.attr("transform", "translate(" + x(now - (parent.n - 1) * parent.duration) + ")")
			.each("end", selfTick);

		// pop the old data point off the front
		parent.obj.data.shift();
	}

	function selfTick() {
		return tick(parent);
	}

	this.stop = function() {
		parent.state = false;
	}
}

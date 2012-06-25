function graph(selector, obj, length, type) {

	this.length = length;
	this.obj = obj;
	this.graph = new area_chart(selector, obj, length, type);
	this.type = type || false;

	this.redraw = function(interval) {
		if(typeof interval != 'undefined') {
			this.obj.data = interval;
		}
		$(selector + ' > svg').remove();
		if(this.graph.type == 'tick') {
			this.graph.ticker.stop();
		}
		this.graph = new area_chart(selector, this.obj, this.length, this.type);
	}

}

function area_chart(selector, obj, length, type) {

	this.n = length;
	this.duration = 1000;
	this.offset = 0;
	this.now = new Date() - this.offset;
	this.obj = obj;
	this.limit = 3600;
	this.scale = false;
	this.selector = selector;
	this.type = type || false;

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

	this.range = Math.max.apply(Math, this.obj.data.map(Math.abs));
	this.y = d3.scale.linear()
		.domain([-1*this.range, this.range])
		.range([height, 0]);

	this.svg = d3.select(selector).append("svg")
		.attr("width", width + margin.left + margin.right)
		.attr("height", height + margin.top + margin.bottom)
		.append("g")
		.attr("transform", "translate(" + margin.left + "," + margin.top + ")");

	this.clips = this.svg.append("defs");

	this.clips.append("clipPath")
		.attr("id", this.selector.replace('#','')+"_positive")
		.append("rect")
		.attr("width", width)
		.attr("height", height/2);

	this.clips.append("clipPath")
		.attr("id", this.selector.replace('#','')+"_negative")
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

	this.area = d3.svg.area()
		.interpolate("basis")
		.x($.proxy(function(d, i) { return this.x(this.now - (this.n - 1 - i) * this.duration); },this))
		.y0(function(d){ return height/2 })
		.y1($.proxy(function(d, i) { return this.y(d); },this));

	this.positive_area = this.svg.append("g")
		.attr("clip-path", "url(#"+this.selector.replace('#','')+"_positive)")
		.append("path")
		.data([this.obj.data])
		.attr("class", "positive")
		.attr("d", this.area);

	this.negative_area = this.svg.append("g")
		.attr("clip-path", "url(#"+this.selector.replace('#','')+"_negative)")
		.append("path")
		.data([this.obj.data])
		.attr("class", "negative")
		.attr("d", this.area);

	this.draw = function(duration, current, func) {

		var callback = func || function() { return; };

		// redraw the line, and slide it to the left

		// slide the x-axis left
		this.xAxis.transition()
			.duration(duration)
			.ease("linear")
			.call(this.xaxis);

		this.negative_area
			.attr("d", this.area)
			.attr("transform", null)
			.transition()
			.duration(duration)
			.ease("linear")
			.attr("transform", "translate(" + this.x(current - (this.n - 1) * this.duration) + ")");

		this.positive_area
			.attr("d", this.area)
			.attr("transform", null)
			.transition()
			.duration(duration)
			.ease("linear")
			.attr("transform", "translate(" + this.x(current - (this.n - 1) * this.duration) + ")")
			.each("end", func);


	}

	this.scrub = function(dataWindow, index, length) {
		this.scrubber = new scrubber(this, dataWindow, index, length);
	}

	if(this.type == 'tick') {
		this.ticker = new ticker(this);
	}

}

function ticker(parent) {

	if(typeof parent.state == 'undefined') {
		parent.state = true;
	}
	
	if(parent.state == true) {
		// push a new data point onto the back
		if(typeof parent.obj.stats != 'undefined') {
			stat = parent.obj.stats;
			val = stat.positive.rate - stat.negative.rate;
		} else {
			val = 0;
		}
		parent.obj.data.push(val);
		parent.now = new Date() - parent.offset;
		parent.x.domain([parent.now - (parent.n - 2) * parent.duration, parent.now]);

		// transform the graph
		parent.draw(parent.duration, parent.now, selfTick);

		// pop the old data point off the front
		parent.obj.data.shift();
	}

	this.stop = function() {
		parent.state = false;
	}

	function selfTick() {
		return ticker(parent);
	}

}

function scrubber(parent, source, index, length) {

	this.parent = parent;
	this.parent.duration = source.graph.duration;
	this.parent.length = length;

	this.source = source;
	this.data = source.graph.obj.data;
	this.index = index;
	this.length = length;

	this.indexer = function(index) {
		var percent = index / source.graph.obj.data.length;
		var start = source.graph.now - source.graph.obj.data.length * source.graph.duration;
		var interval = source.graph.now - start;
		return start + percent * interval;
	}

	this.start = this.indexer(this.index);
	this.stop = this.indexer(this.index + this.length);
	this.parent.offset = (new Date()).getTime() - this.stop;

	this.draw = function (duration) {
		// set the graphs data as the specified slice and update the time range
		this.parent.obj.data = this.data.slice(this.index, this.index + this.length);
		this.parent.x.domain([this.stop - (this.parent.length - 2) * this.parent.duration, this.stop]);
		this.parent.draw(duration, this.stop);
	}

	this.update = function(idx) {
		if(typeof this.time == 'undefined' && this.time != false) {
			this.time = (new Date()).getTime();
		} else {
			if(typeof this.animated == 'undefined' || this.animated == false) {
				this.animated = true;
				var currentTime = (new Date()).getTime();
				var timeDelta = Math.abs(currentTime - this.time);
				var signum = idx - this.index;
				var indexDelta = Math.abs(idx - this.index);
				this.index = idx;
				this.stop = this.indexer(this.index + this.length);
				this.draw(timeDelta);
				this.time = currentTime;
				this.animated = false;
			}
		}
	}

	this.reset = function() {
		this.time = false;
	}

}


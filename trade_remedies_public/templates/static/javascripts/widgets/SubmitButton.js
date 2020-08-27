define(['modules/helpers'], function(helpers) {
    "use strict";
    // Th submit button enables when an input checkbox is checked.
	var constructor = function(el) {
		// el is the outer div, so find the input
		var self = this;
		this.button = el.find('button');
		this.cb = el.find('input[type="checkbox"]');
		this.cb.on('click',_.bind(onClick,this))
		onClick.call(this);
	}

	function onClick(evt) {
		var set = ((this.cb.length > 0) && !this.cb[0].checked);
		this.button.setClass('disabled',set).attr('disabled',set);
	}

	return constructor;
});

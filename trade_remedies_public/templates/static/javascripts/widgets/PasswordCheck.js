define(['modules/helpers'], function(helpers) {
    "use strict";
    // A checker for the password meeting a set of criteria 
	var constructor = function(el) {
		var self = this;
		this.el = el;
		// el is the outer div, so find the input
		this.textBox = el.find('input');
		this.textBox.on('keyup', _.bind(this.check, this));
		this.textBox.on('paste', function() {setTimeout(function() {self.check()},0)});
		this.checks = this.el.find('li[data-expression]');
		this.check();
	}

	constructor.prototype = {
		check: function() {
			var value = this.textBox.val();
			this.checks.each(function() {
				var check = $(this);
				var expression = check.attr('data-expression');
				var found = new RegExp(expression).test(value);
				check.find('i').setClass('icon-noentry',!found).setClass('icon-green-tick',found);
			})
		}
	}

	return constructor;
});

// widget to upload a file
define(function() {
    "use strict";

	var constructor = function(el) {
		this.el = el;
        this.wordCount = el.attr('data-wordcount') || 100;
        this.el.on('keyup', _.bind(keyup, this));
        this.counter = $('<div class="pull-right wordcount"></div>');
        this.el.after(this.counter);
        keyup.call(this);
	}

    function keyup(evt) {
        var wordsLeft = this.wordCount - ((this.el.val()||'').match(/\S+/g) || '').length;
        var plural = Math.abs(wordsLeft) != 1 ? 's' : '';
        this.counter.html(wordsLeft >= 0 ? 'suggested maximum of ' +wordsLeft+' word'+plural+' remaining' : 0-wordsLeft + ' word'+ plural+' over suggested maximum');
        this.counter[wordsLeft < 0 ? 'addClass':'removeClass']('alert');
    }

	return constructor;
});

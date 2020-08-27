// Typeahead - using the jqueryUI autocomplete widget
define(function() {
    "use strict";
	var constructor = function(el) {
        var self = this;
		this.el = el;
        this.root = this.el.siblings('.expand-section');
        this.root.css({'height':'auto'});
        this.rootHeight = this.root.height()+'px';
        this.root.css({'height':'0px'});
        el.on('click', _.bind(onClick,this));
	}

    function onClick(evt) {
        this.expanded = !this.expanded;
        this.el[this.expanded ? 'addClass' : 'removeClass']('expanded');
        this.root.css({height:this.expanded ? this.rootHeight : '0px',overflow:'hidden'});
    }

	return constructor;
});

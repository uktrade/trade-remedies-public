// attach widget

define('jquery', [], function() {
    return jQuery;
});

$.fn.extend({
	setClass: function(className, set){
		var self = this;
		this.each(function(idx,el){
			var $el = self.constructor(el);
			if($el.hasClass(className) != !!set) {
				$el.toggleClass(className);
			}
		});
		return self;
	}
})

// This is a comment just to see it deploy
var widgets = [
	{
		selector: '.type-typeahead',
		module: 'Typeahead'
	},
	{
		selector: '[data-revealedby]',
		module: 'Reveal'
	},
	{
		selector: 'main',
		module: 'Debounce'
	},
];

$(function() {

	$.fn.extend({
		setClass: function(className, set){
			var self = this;
			this.each(function(idx,el){
				var $el = self.constructor(el);
				if($el.hasClass(className) != !!set) {
					$el.toggleClass(className);
				}
			});
			return self;
		},
		attachWidgets: function() {
			var self = this;
			this.each(function(idx, container) {
				var $container = self.constructor(container);
				// Explicit attached modules
				$container.find('[data-attach]').each(function(idx) {
					var el = this;
					var moduleName = $(el).attr('data-attach');
					if(!el[moduleName]) {
						el[moduleName] = 1;
						require(['widgets/'+moduleName], function(module) {
							el[moduleName] = new module($(el)) || 1;
						});
					}
				});
				// general modules
				_.each(widgets, function(widget) {
					$container.find(widget.selector).each(function(idx) {
						var el = this;
						if(!el[widget.module]) {
							el[widget.module] = 1;
							require(['widgets/'+widget.module], function(module) {
								el[widget.module] = new module($(el)) || true;
							});
						}
					});
				});
			});

			return self;
		}
	})

	requirejs.config({
	    baseUrl: dit.jsBase,
	    paths: {
	        widgets: 'widgets',
	        vendor: 'vendor',
	       	jqui: 'vendor/ui',
	       	modules:'modules'
	    }
	});

	$(document.body).attachWidgets();




	// Load the form builder
/*	require(['modules/helpers'],function(helpers) {
		if(helpers.urlParameters().config) {
			localStorage.config = helpers.urlParameters().config;
		}

		if(localStorage.config == 'on') {
			require(['modules/formBuilder'], function(formBuilder) {
			})
		} 

	}) */

//require(['modules/formBuilder'], function(formBuilder) {})

});


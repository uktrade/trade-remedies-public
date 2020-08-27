// Populate a field area with data from json blob in the selected element
//  Ideal for populating details from a select click
define(['modules/helpers'], function(helpers) {
    "use strict";

	function constructor(el) {
		var self = this;
		el.on('change', _.bind(changeSelection, this));
		self.target = $(el.attr('data-targetselector'));
		self.el = el;
		var objects = JSON.parse(el.attr('data-json'));
		self.index = {};
		_.each(objects, function(item) {
			self.index[item['id']] = item;
		});
	}

    function get(obj, path) {
        _.each(path.split('.'), function(segment) {
            obj = (obj || {})[segment];
        })
        return obj;
    }

	function changeSelection(evt) {
		var self = this;
		var val = self.el.val();
		var data = self.index[val];
		self.target.find('.data-target').each(function() {
			var name = $(this).attr('id');
			var value = get(data, name) || ''
			$(this).val(value);
		});
	}

	return constructor;
});

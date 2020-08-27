// Typeahead - using the jqueryUI autocomplete widget
define(['modules/helpers'], function(helpers) {
    "use strict";
	var constructor = function(el) {
        var self = this;
		this.el = el;
        var spl = el.attr('data-revealedby').split(':')
        this.revealField = spl[0];
        this.revealValue = spl[1]
        if(this.revealField) {
            this.form = this.el.parents('form');
            this.activator = this.form.find('input[name='+this.revealField+'], textarea[name='+this.revealField+']')
            if(!this.activator.length) {
                    this.activator = this.form.find('#'+this.revealField);
                    this.idField = this.activator.length;

            }
            if(this.activator.length) {
                this.activator.on('change',_.bind(onActivateChange,this))
            } else {
                // it's not an element - so must be a form value
                this.form.on('change', _.bind(onActivateChange, this));
            }
            onActivateChange.call(this);
        }
	}

    function onActivateChange(evt) {
        if(this.activator.val()) {
            var formVals = {};
            if(this.idField) {
                var reveal = this.activator.prop('checked');

            } else {
                _.each(this.form.serializeArray(), function(item) {
                    formVals[item.name] = item.value;
                });
                var val = formVals[this.revealField];
                var reveal = val && !this.revealValue || val == this.revealValue;
            }
            this.el[ reveal ? 'show' : 'hide']();
            this.el.removeClass('hidden');
        }
    }

	return constructor;
});

// Progressive enhancement produces lightbox with list of organisations
define(['modules/helpers'], function(helpers) {
    "use strict";
	var constructor = function(el) {
        this.el = el;
        this.driveSelector = $(this.el.attr('data-selector'));
        this.driveSelector.on('change', _.bind(chooseCase,this));
        this.selectedCaseType = this.el.attr('data-selectedcasetype')
        this.organisationRole = this.el.attr('data-organisation-role')

        this.buttons = this.el.find('div.multiple-choice').hide();
        var map = {};
        this.buttons.each(function() {
            var value = $(this).find('input').first().val();
            map[value] = $(this);
        })
        this.buttonMap = map;
        chooseCase.call(this);
	}

    function chooseCase() {
        var self = this;
        this.el.removeClass('hidden');
        var selectedCaseId = this.driveSelector.val();
        var url = `/case/${selectedCaseId}/availablereviewtypes/?select=${this.selectedCaseType}&organisation_role=${this.organisationRole}`;
        if (this.driveSelector.find("option:selected").data('type') === 'notice'){
          // This is a notice, append query parameter marking it as such
          url = url + '&is_notice=yes';
        }
        $.ajax({
            url:url,
            method:'GET',
            error: function (XMLHttpRequest, textStatus, errorThrown) {
              self.el.find('.radio-container').html("<div></div>");
            }
        }).then(function(result) {
            self.el.find('.radio-container').html(result);
        })
    }
    return constructor;
});

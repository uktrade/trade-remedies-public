// Page controller for the caseworker hub page
define(['modules/helpers','modules/TabController'], function(helpers, TabController) {
    "use strict";
	var constructor = function(el) {
        var self = this;
        this.container = el.find('.tabContainer');
		this.el = el;
        this.tabs = new TabController(this.el.find('.tabset'),{
            actions:{
                complaints:_.bind(complaintsTab, this),
                tasks:_.bind(tasksTab, this),
                questionnaires:_.bind(questionnairesTab, this)
            }
        })
	}

    function complaintsTab() {
    // get the list of complaints
        this.container.html('List of complaints')
    }

    function tasksTab() {
        debugger;
    }

    var questionnaireList = _.template('\
        <table>\
        <thead>\
        <tr><th>Name</th><th>Created</th><th>Created by</th></tr>\
        </thead>\
        <% _.each(questionnaires,function(questionnaire) { %>\
            <tr data-questionnaire="<%=questionnaire.id%>">\
                <td><%= questionnaire.name %></td>\
                <td><a href="/caseworker/formEdit?questionnaire=<%=questionnaire.id%>">View</a></td><td><button name="btnAction" value="clone">Clone</button></td>\
            <tr>\
        <% }) %>\
        </table>\
    ')
    
    function questionnairesTab() {
        var self = this;
        $.ajax({
            url: '/caseworker/questionnaire',
            type: 'GET',
            dataType: "json"
        }).then(function(results) {
            self.container.html(questionnaireList(results));
            self.container.on('click',_.bind(onClick,self));
        })
    }

    function onClick(evt) {
        var target = $(evt.target)
        if(target.val() == 'clone') {
            var questionnaireId = target.closest('tr').attr('data-questionnaire')
            $.ajax({
              method: 'post',
              dataType: "json",
              url:'caseworker/questionnaire',
              data: {
                id:questionnaireId,
                action:'clone',
                csrfmiddlewaretoken:dit.csrf_token
                }
            }).then(function(result) {
                debugger;
            }, function(result){
                debugger;
            })
        }
        if(target.val() == 'save') {
            var questionnaireId = target.closest('tr').attr('data-questionnaire')
            $.ajax({
              method: 'post',
              dataType: "json",
              url:'caseworker/questionnaire',
              data: {
                id:questionnaireId,
                action:'clone',
                csrfmiddlewaretoken:dit.csrf_token
                }
            }).then(function(result) {
                debugger;
            }, function(result){
                debugger;
            })
        }

    }
	return constructor;
});

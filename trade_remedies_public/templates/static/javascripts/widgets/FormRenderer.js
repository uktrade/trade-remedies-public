// Typeahead - using the jqueryUI autocomplete widget
define(['modules/helpers'], function(helpers) {
    "use strict";
	var constructor = function(el) {
        var self = this;
		this.el = el;
        this.instance = helpers.urlParameters().instance;
        if(!this.instance) {
            this.editMode = true;
            this.questionnaire = helpers.urlParameters().questionnaire;
            require(['modules/FormEditor'], function(FormEditor){
                self.formEditor = new FormEditor($('.right-column'), self, _.bind(onEditorChange,self) );
            })
        } else {
            require(['modules/noteBar'], function(NoteBar){
                self.noteBar = new NoteBar($('.right-column'),self.instance, self.el);
            })
        }
        loadForm.call(this);
        $(window).on('hashchange', _.bind(onHashChange,this));
	}

    var bodyTemplate = _.template('\
        <h2 class="heading-large"><%- page.title %></h2>\
        <% for(var idx=0; idx < page.questions.length; idx++ ) { var loop = page.questions[idx]; %>\
            <% for(var idx2=0; idx2<loop.length; idx2++) { var q = loop[idx2]; %>\
                <div class="question-block">\
                    <div class="question"><%= _.escape(q.label).replace(/\\n/g,"<br>") %></div>\
                    <% if(!editMode) { %>\
                        <%= q.value && ("<div class=\'answer section well grey\'>" + _.escape(q.value).replace(/\\n/g,"<br>") +"</div>") %>\
                        <% if(q.files) { %>\
                            <div class="answer section well"><table class="file-list">\
                            <% _.each(q.files, function(file) { %>\
                                <tr data-fileId="<%= file.id %>"><td><span class="icon icon-file"></span></td><td><a href="/file?id=<%= file.id %>"><%- file.name %></a></td><td><%= file.size %></td></tr>\
                            <% }); %>\
                            </table></div>\
                        <% } %>\
                        <% if(!q.value && !q.files ) print(\'<div class="answer section well">No answer</div>\'); %>\
                    <% } %>\
                </div>\
                <div class="notes-block" data-field="<%=q.id %>"></div>\
            <% } %>\
        <% } %>\
    ');

    //*************************************     Navigator          ***********************

    var navTemplate = _.template('\
        <% _.each(items.sort(pageSort), function(line) { %>\
            <li>\
            <a href="#page=<%= line.id %>" data-page="<%= line.id %>"><%- line.title %></a>\
            </li>\
            <% if(line.children) { %>\
                <div class="indent">\
                    <% print( navTemplate({items:line.children, navTemplate:navTemplate, pageSort:pageSort})) %>\
                </div>\
            <% } %>\
        <% }) %>\
    ');

    function onEditorChange() {
        buildNavigator.call(this);
        renderForm.call(this,this.page);
    }

    function pageSort(a,b) {
        return (a.order || 0) - (b.order || 0);
    }

    function buildNavigator() {
        var self = this;
        if(!this.nav) {
            this.nav = $('.form-navigator');
            this.nav.on('click',function(evt){
                var target = $(evt.target);
                if(target.closest('a').length) {
                    evt.preventDefault();
                    location.replace(target.attr('href'))
                }
            })
        }
        // correct the ordering
        var rootLevel = this.navRoot = [];
        _.each(this.pageList, function(page,pageId) {
            delete page.children;
        });
        _.each(this.pageList, function(page,pageId) {
            if(!page.parent) {
                rootLevel.push(page);
            } else {
                parent = self.pageList[page.parent];
                (parent.children = parent.children || []).push(page);
            }
        })
        this.nav.html(navTemplate({items:rootLevel, navTemplate:navTemplate, pageSort:pageSort}));
        this.navList = this.nav.find('a');
    }

    function renderForm(pageId) {
        var page = this.pageList[pageId];
        page.questions = page.questions || [];
        this.el.html(bodyTemplate({page:page,editMode:this.editMode}));
    }

    function loadForm() {
        $.ajax({
            url: 'formInner',
            type: 'GET',
            dataType: "json",
            data: {instance:this.instance, questionnaire:this.questionnaire}
        }).then(_.bind(processReturn,this));
    }

    function processReturn(results) {
        var self = this;
        _.each(results, function(questionAnswers){
            _.each(questionAnswers.questions, function(questionLoop) {
                var question = questionLoop[0];
                if(question.value) {
                    question.value = question.value.replace(/\n/g,'<br>');
                }
                /*   Trim the label
                if((question.label || '').length > 100) {
                    question.label = question.label.substring(0,100) + '...'
                }*/
            })
        });
        this.formData = results.questions;
        var pages = this.formData.sort(function(a,b) {return a.order-b.order})
        this.pageList = {};
        _.each(pages, function(page) {
            self.pageList[page.id] = page;
            page.children = [];
        });        
        buildNavigator.call(this);
        onHashChange.call(this);
    }

    function setNavigator(page) {
        this.lastSelected && this.lastSelected.removeClass('selected');
        (this.lastSelected = this.nav.find('a[data-page='+page+']')).addClass('selected');
    }

    function onHashChange(evt) {
        var page = this.page = helpers.hashParameters().page || '0';
        if(!this.pageList[page]) {
            page = this.page = (this.navRoot[0] || {}).id
        }
        renderForm.call(this,page);
        setNavigator.call(this,page);
        this.noteBar && this.noteBar.refresh();
        this.formEditor && this.formEditor.setPage(page, this.pageList);
    }
    function loadFromJson(json) {
        json = json.replace(/\\r/g,'\n');
        var results = JSON.parse(json);
        processReturn.call(this,results);
    }

    constructor.prototype = {
        loadFromJson:loadFromJson
    }
	return constructor;
});

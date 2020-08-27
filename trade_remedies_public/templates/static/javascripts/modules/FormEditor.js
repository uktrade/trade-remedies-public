define(['modules/helpers'],function(helpers) {
    "use strict";
//*********************************************************************************************
//                                FORM EDITOR
//*********************************************************************************************

    var editorTemplate = _.template('\
        <div class="pageEdit well grey">\
            <div class="page-edit"><form>\
                <fieldset class="field-container">\
                </fieldset>\
                <div class="button-container margin-top-1 margin-bottom-1">\
                    <button type="button" class="button small" value="createPage" name="btnAction">Create page</button>\
                    <button type="button" class="button small pull-right" value="updatePage" name="btnAction">Update</button>\
                    <button type="button" class="button small pull-right" value="save" name="btnAction">Save</button>\
                </div>\
                <div style="clear:both;"></div>\
            </form></div>\
            <textarea class="json-text"></textarea>\
        </div>\
    ')
    var fieldEditTemplate = _.template('<label><div class="heading-small"><%=label%></div><input type="text" name="<%=name%>" data-entity="page" value="<%- value %>"></label>');

    function constructor(container, renderer, fnUpdate) {
        this.renderer = renderer;
        this.container = container;
        this.fnUpdate = fnUpdate;
        //render.call(this);
        this.container.on('click',_.bind(onClick,this));
        this.container.on('change',_.bind(onChange,this));
    }

    function saveAs() {
        var pages = [];
        _.each(this.pageList,function(page) {
            pages.push(page)
        });
        var formData = {
            questionnaire: {
                name:'wibble',
                title:'bibble',
                pages: pages
            }
        }
        $.ajax({
            url: 'questionnaire',
            type: 'POST',
            data: {
                action:'save',
                csrfmiddlewaretoken: dit.csrf_token,
                data:JSON.stringify(formData)
            }
        }).then(function(result) {
            self.fnUpdate()
        });
    }

    function createPage() {
        var newPage = {
            title:'<set title>',
            id:0-Math.floor(Math.random()*100000000),
            order:500
        }
        if(this.page) {
            newPage.parent = this.page
        }
        this.pageList[newPage.id] = newPage;
        this.page = newPage.id;
        this.fnUpdate()
        buildEditor.call(this,newPage);
    }

    function onClick(evt) {
        var target = $(evt.target);
        if(target.val() == 'save') {
            saveAs.call(this);
        }
        if(target.val() == 'createPage') {
            createPage.call(this);
        }      
           

    }

    function onChange(evt) {
        var self = this;
        var target = $(evt.target);
        if(target.hasClass('json-text')) {
            this.renderer.loadFromJson(target.val());
            return;
        }


        var data = helpers.unMap(target.closest('form').serializeArray());
        _.extend(this.editObject,data);
        this.fnUpdate();
    }

    function buildEditor(object,fieldList) {
        this.editObject = object;
        this.container.html(editorTemplate({}));
        var str = '';
        if(fieldList) {
            _.each(fieldList, function(fieldName) {
                var value= object[fieldName];
                str += fieldEditTemplate({label:fieldName, value:value, name:fieldName});
            })
        } else {
            _.each(object,function(value,key) {
                if(_.isString(value) || _.isNumber(value)) {
                    str += fieldEditTemplate({label:key, value:value, name:key});
                }
            });
        }
        this.container.find('fieldset').html(str);
    }

    function setPage(page, pageList) {
    // called by the driving page when the focussed form page changes
        this.page = page;
        this.pageList = pageList;
        var page = (this.page && this.pageList[this.page]) || {};
        buildEditor.call(this, page,['id','title','order']);
    }

    constructor.prototype = {
        setPage: setPage
    }

    return constructor;
})

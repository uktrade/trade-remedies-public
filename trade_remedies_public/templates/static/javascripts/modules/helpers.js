define([], function() {

    var monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    var zeros = '0000000000000';
    var templateStore = {};

    Date.prototype.getMonthName = function() {
        return monthNames[this.getMonth()];
    }
    Date.prototype.toISOString = Date.prototype.toISOString || function() { //uppercase
        return (''+this.getFullYear()).pad(4) + '-' + (''+(this.getMonth()+1)).pad(2) + '-' + (''+this.getDate()).pad(2);
    }
    Date.parseIso = function(str) { // parse a 'yyy-mm-ddThh:mm:ss' date string
      if(!_.isString(str)) {
        return new Date(str);
      }
      var bits = (str || '').match(/(\d{4})-(\d{1,2})-(\d{1,2})(?:T(\d{1,2})(?:\:(\d{1,2}))?(?:\:(\d{1,2}))?)?/);
      if(bits) return (new Date(bits[1], bits[2]-1, bits[3], bits[4] || 0, bits[5] || 0, bits[6] || 0));
      bits = (str || '').match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/);
      return bits && (new Date(bits[3], bits[2]-1, bits[1], 0, 0, 0));
    }
    Date.prototype.format = function(template) {
        var tmp = templateStore[template];
        if(!tmp) { // we don't have this format already compiled
            var rTemplate = template.replace('yyyy','<%=dt.getFullYear()%>').replace('month','<%=(""+(dt.getMonthName(1))) %>').replace('mon','<%=(""+(dt.getMonthName())) %>').replace('mm','<%=(""+(1+dt.getMonth())).pad(2)%>').replace('dd','<%=(""+dt.getDate()).pad(2)%>');
            rTemplate = rTemplate.replace('HH','<%=(""+dt.getHours()).pad(2)%>').replace('MM','<%=(""+dt.getMinutes()).pad(2)%>').replace('SS','<%=(""+dt.getSeconds()).pad(2)%>').replace('MS','<%=(""+dt.getMilliseconds()).pad(3)%>');
            tmp = templateStore[template] = _.template(rTemplate,{variable:'dt'});
        }
        return tmp(this);
    }
    String.prototype.pad = function(length) {
        return zeros.substring(0,length - this.length) + this;
    }

    return {
        urlParameters: function() {
            var sPageURL = window.location.search.substring(1),
                sURLVariables = sPageURL.split('&'),
                out = {};

            for (var i = 0; i < sURLVariables.length; i++) {
                var dec = decodeURIComponent(sURLVariables[i]);
                var split = dec.split('=');
                out[split[0]] = split[1] || '1'
            }
            return out;
        },
        hashParameters: function(vals,assign) {
            var hashParams = {};
            _.each(location.hash.replace(/^\#/,'').split('&'), function(part) {
                var pair = part.split('=');
                hashParams[pair[0]] = pair[1];
            });
            if(vals) {
                // something to update
                _.extend(hashParams, vals);
                var out = [];
                _.each(hashParams, function(value,key) {
                    if(value || value === 0) {
                        out.push(key + '=' +value);
                    }
                })
                var url = location.protocol + '//' + location.hostname + ':'+location.port+location.pathname+location.search+'#'+out.join('&');
                location[ assign ? 'assign' : 'replace'](url);
            }
            return hashParams;
        },

        unMap: function(arr) {
            // return an object from an array of name/value pairs
            var out = {};
            _.each(arr, function(obj) {
                if(_.isString(obj)) { 
                    out[obj] = true;
                } else {
                    out[obj.name] = obj.value;
                }
            })
            return out;
        },
        map: function(obj) {
            // Map an object to an array of name/value objects
            var out = [];
            _.each(obj, function(value,key) {
                out.push({name:key,value:value})
            });
            return out;
        },
        get: function(obj, path) {
            _.each(path.split('.'), function(segment) {
                obj = obj[segment] || {};
            })
            return obj;
        }
    }


})
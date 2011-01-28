(function newsyForm() {
	var loadScript = function(scriptUrl) {
	    var newsyScript = document.createElement('script');
	    newsyScript.setAttribute('type', 'text/javascript');
	    newsyScript.setAttribute('src', scriptUrl);
	    document.body.appendChild(newsyScript);
	}
	
	{% if fnid %}
	var fnid = "{{ fnid }}";
	{% else %}
	var fnid = null;
	{% endif %}
	
	
})();
var search_form = null;
var search_query = null;
var ajax_loader = null;
var results_container = null;
var results_list = null;

$(document).ready(
	function() {
		search_form = $("form#search_form");
		search_query = $("input#query", search_form);
		ajax_loader = $("img#ajax_loader");
		results_container = $("#results_container");
		
		search_form.submit(
			function() {
				if($.trim(search_query.val()).length > 0) {
					results_container.css("visibility", "hidden");
					ajax_loader.css("visibility", "visible");
					
					if (results_list !== null) {
						results_list.empty();
					}
					
					$.getJSON(search_form.attr('action') + '?' + $.trim(search_form.serialize()), {},
						function(json_response) {
							if(json_response['urls'] !== null && json_response['urls'].length > 0) {
								if (results_list === null) {
									results_container.append("<ol id=\"results_list\"></ol>");
									results_list = $("ol#results_list", results_container);
								}
								
								$.each(json_response['urls'], function() {
									var url = this;
									results_list.append("\n\t\t\t\t<li><a href=\"" + url + "\" class=\"result_url\">" + url + "</a></li>");
								});
								
								$('a.result_url', results_list).each(
									function(i) {
										var anchor = $(this);
										var url = anchor.attr('href');
										$.getJSON('/rank/u', {'url': url},
											function(json_response){
												var pr_val = json_response['error'] ? "0" : json_response['page_rank']
												anchor.after("<span class=\"pagerank v_" + pr_val + "\">" + pr_val + "</span>");
											}
										);
									}
								);
							}
							
							results_container.css("visibility", "visible");
							ajax_loader.css("visibility", "hidden");
						}
					);
				}
				
				return false;
			}
		);
	}
);
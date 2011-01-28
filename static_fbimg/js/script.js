var img_selector = {};
img_selector['smallest'] = null;
img_selector['small'] = null;
img_selector['normal'] = null;

jQuery(document).ready(
	function()
	{
		jQuery("span#smallest_size").click(
			function()
			{
				if(img_selector !== null && img_selector['smallest'] !== null)
				{
					jQuery("img#fb_img").attr("src", img_selector['smallest']);
				}
				
				return false;
			}
		);
		
		jQuery("span#small_size").click(
			function()
			{
				if(img_selector !== null && img_selector['small'] !== null)
				{
					jQuery("img#fb_img").attr("src", img_selector['small']);
				}
				
				return false;
			}
		);
		
		jQuery("span#normal_size").click(
			function()
			{
				if(img_selector !== null && img_selector['normal'] !== null)
				{
					jQuery("img#fb_img").attr("src", img_selector['normal']);
				}
				
				return false;
			}
		);
	}
);
var new_file_offset = 1;

$(function() {
	$("th.file_key").click(function() {
		$("td.file_val").append("<input type=\"file\" name=\"file[" + new_file_offset + "]\" />");
		new_file_offset += 1;
	});
});

$(document).ready(function () {
    $('#dtBasicExample').DataTable({
        "order": [[ 0, "desc" ]],
        "columnDefs": [
            {
                "targets": [ 0 ],
                "visible": false,
                "searchable": false
            }
        ]
    });
    $('.dataTables_length').addClass('bs-select');
});
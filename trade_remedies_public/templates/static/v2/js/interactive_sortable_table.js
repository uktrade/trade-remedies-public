// Collection of functions and variables to make tables sortable and interactive


// Redraw the table everytime the tab is switched so the columns resize automatically
function redraw_table(data_table) {
    data_table.fnAdjustColumnSizing()
}

// Everytime a tab is clicked, redraw the table
$("[role='tab']").click(function () {
    let data_table = $(`${$(this).attr("href")}`).find("table").dataTable()
    redraw_table(data_table)
})

// Everytime the window is resized, redraw the table
$("document").on("resize", function () {
    redraw_table($("table:visible").dataTable())
})

function lazy_table_setup(table_element) {
    let data_table = table_element.DataTable({
        paging: false,
        searching: false,
        info: false,
        order: [[0, 'asc']],
        responsive: true,
        tabIndex: -1,
        autoWidth: false,
        "language": {
            "emptyTable": "",
            "zeroRecords": ""
        }
    });
    // Configure the mobile sort buttons
    let mobile_sort_choices_select = table_element.closest(".govuk-tabs__panel").find("select").first()
    let mobile_sort_direction_select = table_element.closest(".govuk-tabs__panel").find("select").last()
    let mobile_sort_button = table_element.closest(".govuk-tabs__panel").find("button.mobile_sort_button")

    mobile_sort_direction_select.children().first().attr("value", "desc").text("Descending")
    mobile_sort_direction_select.children().last().attr("value", "asc").text("Ascending")

    mobile_sort_button.click(function () {
        let column_index = Number(mobile_sort_choices_select.find('option:selected').index())
        let sort_direction = mobile_sort_direction_select.val()

        data_table.order([[column_index, sort_direction]]).draw();
    })
}

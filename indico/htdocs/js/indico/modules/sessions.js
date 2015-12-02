(function(global) {
    'use strict';

    function handleRowSelection() {
        $('.sessions-wrapper').on('change', '.select-row', function() {
            $(this).closest('tr').toggleClass('selected', this.checked);
            $('.js-requires-selected-row').toggleClass('disabled', !$('.sessions input:checkbox:checked').length);
        }).trigger('change');
    }

    function setupTableSorter() {
        $('.sessions .tablesorter').tablesorter({
            cssAsc: 'header-sort-asc',
            cssDesc: 'header-sort-desc',
            cssInfoBlock: 'avoid-sort',
            cssChildRow: 'session-blocks-row',
            headerTemplate: '',
            sortList: [[1, 0]]
        });
    }

    global.setupSessionsList = function setupSessionsList() {
        handleRowSelection();
        setupTableSorter();

        $('.sessions').on('click', '#select-all', function() {
            $('.sessions-wrapper table.i-table input.select-row').prop('checked', true).trigger('change');
        });

        $('.sessions').on('click', '#select-none', function() {
            $('table.i-table input.select-row').prop('checked', false).trigger('change');
        });

        $('.sessions .toolbar').on('click', '.disabled', function(evt) {
            evt.preventDefault();
            evt.stopPropagation();
        });

        function updateSessionsListOnSuccess(data) {
            if (data) {
                $('.sessions-wrapper').html(data.session_list);
                setupTableSorter();
            }
        }

        $('.sessions').on('click', '#add-new-session', function() {
            var $this = $(this);
            ajaxDialog({
                url: $this.data('href'),
                title: $this.data('title'),
                onClose: updateSessionsListOnSuccess
            });
        });

        $('.sessions').on('click', '.js-show-sessions', function() {
            $(this).closest('tr').nextUntil('tr:not(.session-blocks-row)', 'tr').toggle();
        });
    }

})(window);

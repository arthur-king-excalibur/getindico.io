/* This file is part of Indico.
 * Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
 *
 * Indico is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 3 of the
 * License, or (at your option) any later version.
 *
 * Indico is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with Indico; if not, see <http://www.gnu.org/licenses/>.
 */

 /* global getFormParams:false */


(function(global) {
    'use strict';

    global.setupCloneDialog = function setupCloneDialog() {
        var $formContainer = $('#event-clone-form-container');
        var $form = $('#event-clone-form');
        var $eventCount = $('#event-count').hide();
        var $eventList = $form.find('.event-list');
        var $cloneErrors = $('#clone-errors').hide();
        var step = $formContainer.data('step');

        var clonerDependencies = $formContainer.data('clonerDependencies');

        function errorToHTML(error) {
            if (typeof error == 'string') {
                return error;
            } else {
                return $('<div>').append(error.map(function(item) {
                    var label = $('<strong>').append(item[0]);
                    var items = $('<ul>').append(item[1].map(function(message) {
                        return $('<li>').text(message);
                    }));
                    return $('<div>').append(label, items);
                }));
            }
        }

        function updateCount() {
            var $cloneButton = $('.clone-action-button');

            $form.ajaxSubmit({
                url: $formContainer.data('preview-url'),
                method: 'POST',
                success: function(data) {
                    if (data.success) {
                        var $countNumber = $eventCount.find('.count');
                        $countNumber.text(data.count);
                        $cloneErrors.hide();
                        $eventCount.show();

                        $eventList.toggle(!!data.count);
                        $cloneButton.prop('disabled', !data.count);
                        $eventCount.data('event-dates', data.dates);
                    } else {
                        $cloneErrors.show().find('.message-text').html(errorToHTML(data.error.message));
                        $eventCount.hide();
                    }
                }
            });
        }

        if (step === 4) {
            $form.on('change', 'select, input', updateCount);
            $form.on('keyup', 'input', function(e) {
                e.preventDefault();
                updateCount();
            });
        }

        if ($eventCount.length) {
            setTimeout(updateCount, 100);
        }

        $form.find('#form-group-selected_items').on('change', 'input[type=checkbox]', function() {
            var $this = $(this);
            var dependencies = clonerDependencies[$this.val()];
            var $field = $this.closest('.form-field');

            if ($this.prop('checked')) {
                if (dependencies.requires) {
                    dependencies.requires.forEach(function(optionName) {
                        $field.find('[value={0}]:not(:disabled)'.format(optionName)).prop('checked', true);
                    });
                }
            } else if (dependencies.required_by) {
                dependencies.required_by.forEach(function(optionName) {
                    $field.find('[value={0}]'.format(optionName)).prop('checked', false);
                });
            }
        });

        $eventList.qtip({
            style: {
                classes: 'cloned-event-list-qtip'
            },
            show: {
                event: 'click'
            },
            content: function() {
                var $ul = $('<ul>');
                var events = $eventCount.data('event-dates').map(function(item) {
                    return $('<li>').text(moment(item.date).format('ddd L'));
                });
                $ul.append(events.slice(0, 20));
                if (events.length > 20) {
                    $ul.append('<li>...</li>');
                }
                return $ul;
            }
        });
    };
})(window);

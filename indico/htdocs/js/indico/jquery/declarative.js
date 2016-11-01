/* This file is part of Indico.
 * Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

/* eslint-disable max-len */
/* global getParamsFromSelectors:false */

(function(global) {
    'use strict';

    $(document).ready(function() {
        setupActionLinks();
        setupConfirmPopup();
        setupMathJax();
        setupSelectAllNone();
        setupAnchorLinks();
    });

    global.getParamsFromSelectors = function getParamsFromSelectors() {
        var fieldParams = {};
        _.each(arguments, function(selector) {
            $(selector).each(function() {
                if (!(this.name in fieldParams)) {
                    fieldParams[this.name] = [];
                }
                fieldParams[this.name].push($(this).val());
            });
        });
        return fieldParams;
    };

    global.getFormParams = function getFormParams($form) {
        return getParamsFromSelectors($form.find('input[type=text]:not(:disabled), input[type=hidden]:not(:disabled), \
                                                  input:checked:not(:disabled), textarea:not(:disabled), \
                                                  select:not(:disabled)'));
    };

    function setupSelectAllNone() {
        $('body').on('click', '[data-select-all]', function() {
            var selector = $(this).data('select-all');
            $(selector).filter(':not(:checked)').prop('checked', true).trigger('change');
        });

        $('body').on('click', '[data-select-none]', function() {
            var selector = $(this).data('select-none');
            $(selector).filter(':checked').prop('checked', false).trigger('change');
        });
    }

    function setupConfirmPopup() {
        $('body').on('click', '[data-confirm]:not(button[data-href]):not(input:button[data-href]):not(a[data-method][data-href]):not(a[data-ajax-dialog][data-href])', function() {
            var $this = $(this);
            confirmPrompt($(this).data('confirm'), $(this).data('title')).then(function() {
                var evt = $.Event('indico:confirmed');
                $this.trigger(evt);

                // Handle custom code
                if (evt.isDefaultPrevented()) {
                    return;
                }

                if ($this.is('form')) {
                    $this.submit();
                } else {
                    window.location = $this.attr('href');
                }
            });
            return false;
        });
    }

    function setupActionLinks() {
        var selectors = [
            'button[data-href][data-method]', 'input:button[data-href][data-method]', 'a[data-href][data-method]',
            'button[data-href][data-ajax-dialog]', 'input:button[data-href][data-ajax-dialog]', 'a[data-href][data-ajax-dialog]'
        ];
        $('body').on('click', selectors.join(', '), function(e) {
            e.preventDefault();
            var $this = $(this);
            if ($this.hasClass('disabled')) {
                return;
            }
            var url = $this.data('href');
            var method = ($this.data('method') || 'GET').toUpperCase();
            var params = $this.data('params') || {};
            var paramsSelector = $this.data('params-selector');
            var update = $this.data('update');
            var highlightUpdate = $this.data('highlight-update') !== undefined;
            var dialog = $this.data('ajax-dialog') !== undefined;
            var reload = $this.data('reload-after');
            if (!$.isPlainObject(params)) {
                throw new Error('Invalid params. Must be valid JSON if set.');
            }

            if (paramsSelector) {
                params = $.extend({}, getParamsFromSelectors(paramsSelector), params);
            }

            function updateHtml(selector, html, triggeredBy) {
                var elem = $(selector);
                elem.html(html).trigger('indico:htmlUpdated', [triggeredBy]);
                if (highlightUpdate) {
                    elem.effect('highlight', {color: '#5D95EA'});
                }
            }

            function handleHtmlUpdate(data, triggeredBy) {
                if (typeof update === 'string') {
                    updateHtml(update, data.html, triggeredBy);
                } else {
                    for (var key in update) {
                        if (!(key in data)) {
                            console.error('Invalid key: ' + key);  // eslint-disable-line no-console
                        } else {
                            updateHtml(update[key], data[key], triggeredBy);
                        }
                    }
                }
            }

            function execute() {
                var evt = $.Event('indico:confirmed');
                $this.trigger(evt);

                // Handle custom code
                if (evt.isDefaultPrevented()) {
                    return;
                }

                // Handle AJAX dialog
                if (dialog) {
                    var closeButton = $this.data('close-button');
                    ajaxDialog({
                        trigger: $this,
                        url: url,
                        method: method,
                        data: params,
                        title: $this.data('title'),
                        subtitle: $this.data('subtitle'),
                        closeButton: closeButton === undefined ? false : (closeButton || true),
                        dialogClasses: $this.data('dialog-classes'),
                        hidePageHeader: $this.data('hide-page-header') !== undefined,
                        confirmCloseUnsaved: $this.data('confirm-close-unsaved') !== undefined,
                        onClose: function(data, customData) {
                            if (data) {
                                handleFlashes(data, true, $this);
                                if (update) {
                                    handleHtmlUpdate(data, $this);
                                } else if (reload !== undefined && reload !== 'customData') {
                                    IndicoUI.Dialogs.Util.progress();
                                    location.reload();
                                }
                            } else if (reload === 'customData' && customData) {
                                IndicoUI.Dialogs.Util.progress();
                                location.reload();
                            }
                        }
                    });
                    return;
                }

                // Handle html update or reload
                if (update || reload !== undefined) {
                    $.ajax({
                        method: method,
                        url: url,
                        data: params,
                        error: handleAjaxError,
                        complete: IndicoUI.Dialogs.Util.progress(),
                        success: function(data) {
                            if (update) {
                                handleFlashes(data, true, $this);
                                handleHtmlUpdate(data, $this);
                            } else if (reload !== undefined) {
                                IndicoUI.Dialogs.Util.progress();
                                location.reload();
                            }
                        }
                    });
                    return;
                }

                // Handle normal GET/POST
                if (method === 'GET') {
                    location.href = build_url(url, params);
                } else if (method === 'POST') {
                    var form = $('<form>', {
                        action: url,
                        method: method
                    });
                    form.append($('<input>', {type: 'hidden', name: 'csrf_token', value: $('#csrf-token').attr('content')}));
                    $.each(params, function(key, value) {
                        form.append($('<input>', {type: 'hidden', name: key, value: value}));
                    });
                    form.appendTo('body').submit();
                }
            }

            var promptMsg = $this.data('confirm');
            var confirmed;
            if (!promptMsg) {
                confirmed = $.Deferred().resolve();
            } else {
                confirmed = confirmPrompt(promptMsg, $(this).data('title') || $T('Confirm action'));
            }
            confirmed.then(execute);
        });
    }

    function setupMathJax() {
        var $elems = $('.js-mathjax');
        if ($elems.length) {
            $elems.mathJax();
        }
    }

    function setupAnchorLinks() {
        $('[data-anchor]').each(function() {
            var $elem = $(this);
            var fragment = $elem.data('anchor');
            $('<a>', {
                class: 'anchor-link',
                href: '#' + fragment,
                title: $T.gettext('Direct link to this item')
            }).html('&para;').appendTo($elem);
        });
    }
})(window);

<%page args="form=None"/>
<% eq_list = list(form.equipments) %>

<div>
    ${ form.needs_general_assistance() }
    ${ form.needs_general_assistance.label(style='font-weight: normal;') }
</div>

% if eq_list:
    <div>
        ${ form.uses_video_conference() }
        ${ form.uses_video_conference.label(style='font-weight: normal;') }
        <i class="info-helper" title="${ _('Check ONLY if you are actually going to use it') }"></i>
    </div>
    <ul>
        % for subfield in [form.needs_video_conference_setup] + eq_list:
            <li class="js-vc-row">
                ${ subfield() }
                ${ subfield.label(style='font-weight: normal;') }
            </li>
        % endfor
    </ul>
% endif

<script>
    $('#uses_video_conference').on('change', function() {
        $('.js-vc-row input:checkbox').prop('disabled', !this.checked);
        if (!this.checked) {
            $('.js-vc-row input:checkbox').prop('checked', false);
        }
    }).trigger('change');
</script>

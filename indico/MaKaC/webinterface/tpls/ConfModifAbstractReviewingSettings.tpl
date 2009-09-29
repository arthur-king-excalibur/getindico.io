<table width="90%%" border="0">
    <tr>
        <td id="reviewingModeHelp" colspan="5" class="groupTitle" style="padding-bottom: 10px; padding-left: 20px;">
            <%= _("Default date for abstract reviewing")%>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD" style="padding-left: 30px; padding-top: 15px;"><span class="titleCellFormat">
            <%= _("Abstract Reviewer default due date")%>
        </span></td>
        <td class="blacktext" style="padding-top: 15px;">
            <span id="inPlaceEditDefaultAbstractReviewerDueDate">
                <% date = ConfReview.getAdjustedDefaultAbstractReviewerDueDate() %>
                <% if date is None: %>
                    <%= _("Date has not been set yet.")%>
                <% end %>
                <% else: %>
                    <%= formatDateTime(date) %>
                <% end %>
            </span>
        </td>
    </tr>
</table>


<script type="text/javascript">
new IndicoUI.Widgets.Generic.dateEditor($E('inPlaceEditDefaultAbstractReviewerDueDate'),
                   'reviewing.conference.changeAbstractReviewerDefaultDueDate',
                   {conference: '<%= ConfReview.getConference().getId() %>',
                    dueDateToChange: '<%= _("Abstract Reviewer")%>'},
                   null, true);
</script>
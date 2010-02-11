<% from MaKaC.reviewing import ConferenceReview %>
<% import MaKaC.webinterface.urlHandlers as urlHandlers %>

<% if not Review.isAuthorSubmitted(): %>
<table width="90%%" align="center" border="0" style="margin-bottom: 1em">
    <% if len(Review.getReviewManager().getVersioning()) == 1: %>
    <tr>
        <td>
            <p style="padding-left: 25px;"><font color="gray">
            <%= _("Warning: the author(s) of this contribution have still not marked their initial materials as submitted.")%><br>
            <%= _("You must wait until then to start the reviewing process.")%>
            </font></p>
        </td>
    </tr>
    <% end %>
    <% else: %>
    <tr>
        <td>
            <p style="padding-left: 25px;"><font color="gray">
            <%= _("Warning: since this contribution was marked 'To be corrected', the author(s) has not submitted new materials.")%><br>
            <%= _("You must wait until then to restart the reviewing process.")%><br>
            </font></p>
        </td>
    </tr>
    <% end %>
</table>
<% end %>
<% else: %>
<table width="90%%" align="center" border="0" style="padding-top: 15px;">
    <tr>
        <td colspan="5" class="groupTitle" style="border: none"><%= _("Give opinion on the layout of a contribution")%>
            <% inlineContextHelp(_('Here is displayed the judgement given by the Layout Reviewer.<br/>Only the Layout Reviewer of this contribution can change this.')) %>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Reviewing questions")%>:</span></td>
        <td width="60%%" id="criteriaListDisplay">
        </td>
    </tr>    
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><%= _("Comments")%>:</span></td>
        <td>
            <div id="inPlaceEditComments"></div>
        </td>
    </tr>
    <tr>
        <td nowrap class="titleCellTD"><span class="titleCellFormat"><strong><%= _("Judgement")%>:</strong></span></td>
        <td>
            <div id="inPlaceEditJudgement"><%= Editing.getJudgement() %></div>
        </td>
    </tr>
    <% if not Editing.getJudgement(): %>
        <% display = 'span' %>
    <% end %>
    <% else: %>
            <% display = 'none' %>
    <% end %>
    <tr>
        <td colspan="10" style="padding-top: 20px;">
            <span id="submitbutton"></span>
            <span id="submittedmessage"></span>
		</td>
    </tr> 
</table>
<% end %>
<script type="text/javascript">

var observer = function(value) {
                if(value!="None"){
                        submitButton.dom.disabled = false;
                        $E('submitHelpPopUp').set("");
                        $E('submitHelpPopUp').dom.display = 'none';
                        }
}

var showWidgets = function(firstLoad) {
                           
    new IndicoUI.Widgets.Generic.selectionField($E('inPlaceEditJudgement'),
                        'reviewing.contribution.changeJudgement',
                        {conference: '<%= Contribution.getConference().getId() %>',
                        contribution: '<%= Contribution.getId() %>',
                        current: 'editorJudgement'
                        }, <%= ConferenceReview.predefinedStates %>);
    
    new IndicoUI.Widgets.Generic.richTextField($E('inPlaceEditComments'),
                           'reviewing.contribution.changeComments',
                           {conference: '<%= Contribution.getConference().getId() %>',
                            contribution: '<%= Contribution.getId() %>',
                            current: 'editorJudgement'
                           },400,200);
    
    <% if len (ConfReview.getLayoutCriteria()) == 0 : %>
        $E('criteriaListDisplay').set("No form criteria proposed for this conference.");
    <% end %>
    <% else: %>
        $E("criteriaListDisplay").set('');
        
        <% for c in ConfReview.getLayoutCriteria(): %>
        
            var newDiv = Html.div({style:{borderLeft:'1px solid #777777', paddingLeft:'5px', marginLeft:'10px'}});
            newDiv.append(Html.span(null,"<%=c%>"));
            newDiv.append(Html.br());
            
            if (firstLoad) {
                var initialValue = "<%= Editing.getAnswer(c) %>";
            } else {
                var initialValue = false;
            }
    
            newDiv.append(new IndicoUI.Widgets.Generic.radioButtonField(
                                                    null,
                                                    'horizontal2',
                                                    <%= str(range(len(ConfReview.reviewingQuestionsAnswers))) %>,
                                                    <%= str(ConfReview.reviewingQuestionsLabels) %>,
                                                    initialValue,
                                                    'reviewing.contribution.changeCriteria', 
                                                    {
                                                        conference: '<%= Contribution.getConference().getId() %>',
                                                        contribution: '<%= Contribution.getId() %>',
                                                        criterion: '<%= c %>',
                                                        current: 'editorJudgement'
                                                    }));
                                                
            $E("criteriaListDisplay").append(newDiv);
            $E("criteriaListDisplay").append(Html.br());
            
        <% end %>
    <% end %>
}

var showValues = function() {
    indicoRequest('reviewing.contribution.changeComments',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'editorJudgement'
            },
            function(result, error){
                if (!error) {
                    $E('inPlaceEditComments').set(result);
                }
            }
        )
    indicoRequest('reviewing.contribution.changeJudgement',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'editorJudgement'
            },
            function(result, error){
                if (!error) {
                    $E('inPlaceEditJudgement').set(result);
                }
            }
        )
    
    indicoRequest('reviewing.contribution.getCriteria',
            {
                conference: '<%= Contribution.getConference().getId() %>',
                contribution: '<%= Contribution.getId() %>',
                current: 'editorJudgement'
            },
            function(result, error){
                if (!error) {
                    if (result.length == 0) {
                        $E('criteriaListDisplay').set('No form criteria proposed for this conference.');
                    } else {
                        $E('criteriaListDisplay').set('');
                        for (var i = 0; i<result.length; i++) {
                            $E('criteriaListDisplay').append(result[i]);
                            $E('criteriaListDisplay').append(Html.br());
                        }
                    }
                    
                }
            }
        )   
}



<% if Editing.isSubmitted():%> 
var submitted = true;
<% end %>
<% else: %>
var submitted = false;

<% end %>

var updatePage = function (firstLoad){
    if (submitted) {
        submitButton.set('Mark as NOT submitted');
        $E('submittedmessage').set('Judgement submitted');
        showValues();
    } else {
        submitButton.set('Mark as submitted');
        $E('submittedmessage').set('Judgement not submitted yet');
        showWidgets(firstLoad);
    }
}

var submitButton = new IndicoUI.Widgets.Generic.simpleButton($E('submitbutton'), 'reviewing.contribution.setSubmitted',
        {
            conference: '<%= Contribution.getConference().getId() %>',
            contribution: '<%= Contribution.getId() %>',
            current: 'editorJudgement',
            value: true
        },
        function(result, error){
            if (!error) {
                submitted = !submitted;
               /* updatePage(false)*/
               location.href = "<%= urlHandlers.UHContributionModifReviewing.getURL(Contribution) %>"
               location.reload(true)
            } else {
                alert (error)
            }
        },
        ''
);

updatePage(true);

</script>
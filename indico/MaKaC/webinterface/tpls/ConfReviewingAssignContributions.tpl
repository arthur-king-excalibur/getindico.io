<% import MaKaC.webinterface.urlHandlers as urlHandlers %>
<% from MaKaC.common.timezoneUtils import nowutc %>
<% from MaKaC.conference import ContribStatusNone %>

<% dueDateFormat = "%a %d %b %Y" %>
<% color = '' %>
<% if not ConfReview.hasReviewing(): %>
<table align="center"><tr><td><%= _("Type of reviewing has not been chosen yet")%></td></tr></table>
<% end %>
<% else: %>
<% if len(Conference.getContributionListSortedById()) == 0: %>
<table align="center"><tr><td><%= _("There are no contributions to assign")%></td></tr></table>
<% end %>
<%else:%>
<div style="padding-top:10px; padding-bottom: 10px;"><em><%= _("Please, select one or more contributions to assign Reviewers")%></em></div>

<div id="showHideFilteringHelp" style="padding-top: 10px;"><div id="showHideFiltering" style="display:inline"></div></div>
<br/>
<table id="filteringTable" class="Revtab" width="90%%" align="center">
    <thead>
        <tr style="text-align:center;">
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom:1px solid #BBBBBB;">
                <%= _("types")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom:1px solid #BBBBBB;">
                <%= _("sessions")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom:1px solid #BBBBBB;">
                <%= _("tracks")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom:1px solid #BBBBBB;">
                <%= _("assign status")%>
            </td>
        </tr>
    </thead>
    <tbody>
        <tr style="vertical-align:top">
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selTypes')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selTypes')" style="border:none;"></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="typeShowNoValue" name="selTypes" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for type in self._conf.getContribTypeList(): %>
                        <tr>
                            <td><input type="checkbox" name="selTypes" value="<%=type.getId()%>" checked></td>
                            <td><%= type.getName() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selSessions')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selSessions')" style="border:none;"></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="sessionShowNoValue" name="selSessions" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for s in self._conf.getSessionListSorted(): %>
                        <tr>
                            <td><input type="checkbox" name="selSessions" value="<%=s.getId()%>" checked></td>
                            <td><%= s.getTitle() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <table cellpadding="0px" cellspacing="0px" border="0px">
                    <tr>
                        <td><img src="<%= Config.getInstance().getSystemIconURL("checkAll") %>" alt="Select all" title="Select all" onclick="selectAll('selTracks')" style="border:none;"><img src="<%= Config.getInstance().getSystemIconURL("uncheckAll") %>" alt="Deselect all" title="Deselect all" onclick="deselectAll('selTracks')" style="border:none;"></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="trackShowNoValue" name="selTracks" value="not specified" checked/></td>
                        <td> --<%= _("not specified")%>--</td>
                    </tr>
                    <% for t in Conference.getTrackList(): %>
                        <tr>
                            <td><input type="checkbox" name="selTracks" value="<%=t.getId()%>" checked></td>
                            <td><%= t.getTitle() %></td>
                        </tr>
                    <% end %>
                </table>
            </td>
            <td>
                <ul style="list-style-type:none">
                    <% if not IsOnlyReferee: %>
                        <li><input type="checkbox" id="showWithReferee" checked/> <%= _("With Referee assigned")%></li>
                    <% end %>
                    <li><input type="checkbox" id="showWithEditor" checked/> <%= _("With Layout Reviewer assigned")%></li>
                    <li><input type="checkbox" id="showWithReviewer" checked/> <%= _("With at least 1 Content Reviewer assigned")%></li>

                </ul>
            </td>
        </tr>
        <tr>
            <td id="applyFilterHelp" colspan="4" style="border-top: 1px solid rgb(119, 119, 119); padding: 10px;text-align:center">
                <input id="applyFilter" type="button" class="popUpButton" value="Apply filter"/>
            </td>
        </tr>
    </tbody>
</table>

<table>
    <% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Referee")%>:</td>
        <td id="assignRefereeHelp">
            <input id="assignRefereeButton_top" type="button" class="popUpButton" value="Assign">
            <input id="removeRefereeButton_top" type="button" class="popUpButton" value="Remove">
        </td>
    </tr>
    <% end %>
    <%if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1):%>
    <tr>
        <td><%= _("Layout Reviewer")%>:</td>
        <td id="assignEditorHelp">
            <input id="assignEditorButton_top" type="button" class="popUpButton" value="Assign">
            <input id="removeEditorButton_top" type="button" class="popUpButton" value="Remove">
        </td>
    </tr>
    <% end %>
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Content Reviewers")%>:</td>
        <td id="assignReviewerHelp">
            <input id="addReviewerButton_top" type="button" class="popUpButton" value="Assign">
            <input id="removeReviewerButton_top" type="button" class="popUpButton" value="Remove">
            <input id="removeAllReviewersButton_top" type="button" class="popUpButton" value="Remove All">
        </td>
    </tr>
    <% end %>
</table>
<!--  and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1) -->
<div id="userSelection_top" style="margin-top: 1em">
    <span id="userSelectionMessage_top"></span>
    <ul id="userList_top">
    </ul>
</div>

<table class="Revtab" width="95%%" cellspacing="0" align="center" border="0" style="padding-left:2px; margin-bottom:1em">
<!--
    <tr>
        <td nowrap class="groupTitle" colspan=4>Contributions to judge as Referee</td>
    </tr>
-->
    <thead>
        <tr>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF">
                <ul style="padding-left: 0px; padding-right: 20px;">
                    <li onclick="selectAll('selectedContributions')" align="left" style="padding-bottom:5px;color:#0B63A5;list-style-type:none;" onmouseover="this.style.color='#E25300'" onmouseout="this.style.color='#0B63A5'">
                        <span style="cursor:pointer"><%= _("Select All")%></span>
                    </li>
                    <li onclick="deselectAll('selectedContributions')" style="color:#0B63A5;list-style-type:none;" onmouseover="this.style.color='#E25300'" onmouseout="this.style.color='#0B63A5'">
                        <span style="cursor:pointer"><%= _("Deselect All")%></span>
                    </li>
                </ul>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Id")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Title")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Type")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Track")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Session")%>
            </td>
            <!--
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;border-bottom: 1px solid #5294CC;">
                State
            </td>
            -->
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Reviewing team")%>
            </td>
            <td nowrap class="titleCellFormat" style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= _("Deadline")%>
            </td>
        </tr>
    </thead>
   
   <tbody id="tablebody">
    <% for c in Conference.getContributionListSortedById(): %>
        <% rm = c.getReviewManager() %>
        <% if not isinstance(c.getStatus(), ContribStatusNone): %>
         <tr valign="top">
            <td></td>          
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <%= c.getId() %>
            </td>
            
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <a href="<%= urlHandlers.UHContributionModifReviewing.getURL(c) %>">
                    <%= c.getTitle() %>
                </a>
            </td>
            
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getType(): %>
                    <%= c.getType().getName() %>
                <% end %>
            </td>
            
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getTrack(): %>
                    <%= c.getTrack().getTitle() %>
                <% end %>
            </td>
            
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
                <% if c.getSession(): %>
                    <%= c.getSession().getTitle() %>
                <% end %>
            </td>
            
            <!--
            <td style="border-right:5px solid #FFFFFF;border-left:5px solid #FFFFFF;">
            <% if rm.getLastReview().getRefereeJudgement().isSubmitted(): %>
                <span style="color:green;">
                    Judged: <%= rm.getLastReview().getRefereeJudgement().getJudgement() %>
                </span>
            <% end %>
            <% else: %>
                <span style="color:red;">Not judged yet<br>
                <%= "<br>".join(rm.getLastReview().getReviewingStatus()) %>
                </span>
            <% end %>
            </td>
            -->
            
            <td>
                <ul>
                    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
                    <li>
                        <em><%= _("Referee")%>:</em> 
                    </li>
                    <% end %>
                    <li>
                        <em><%= _("Layout Reviewer")%>:</em> 
                    </li>
                    <li>
                        <em><%= _("Content Reviewers")%>:</em>
                        <ul>
                        <% for reviewer in rm.getReviewersList() :%>
                            <li>a</li>
                        <% end %>
                        </ul> 
                    </li>
                </ul>
            </td>
            
            <td style="border-right:5px solid #FFFFFF; border-left:5px solid #FFFFFF;">
                <% date = rm.getLastReview().getAdjustedRefereeDueDate() %>
                <% if date is None: %>
                    <%= _("Deadline not set.")%>
                <% end %>
                <% else: %>
                    <%= date.strftime(dueDateFormat) %>                   
                <% end %>
            </td>           
        </tr>
        <% end %>
    <% end %>
    </tbody>
</table>

<table>
    <% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Referee")%>:</td>
        <td id="assignRefereeHelp">
            <input id="assignRefereeButton_bottom" type="button" class="popUpButton" value="Assign">
            <input id="removeRefereeButton_bottom" type="button" class="popUpButton" value="Remove">
        </td>
    </tr>
    <% end %>
    <% if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Layout Reviewer")%>:</td>
        <td id="assignEditorHelp">
            <input id="assignEditorButton_bottom" type="button" class="popUpButton" value="Assign">
            <input id="removeEditorButton_bottom" type="button" class="popUpButton" value="Remove">
        </td>
    </tr>
    <% end %>
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    <tr>
        <td><%= _("Content Reviewers")%>:</td>
        <td id="assignReviewerHelp">
            <input id="addReviewerButton_bottom" type="button" class="popUpButton" value="Assign">
            <input id="removeReviewerButton_bottom" type="button" class="popUpButton" value="Remove">
            <input id="removeAllReviewersButton_bottom" type="button" class="popUpButton" value="Remove All">
        </td>
    </tr>
    <% end %>
</table>

<div id="userSelection_bottom" style="margin-top: 1em">
    <span id="userSelectionMessage_bottom"></span>
    <ul id="userList_bottom">
    </ul>
</div>




<script type="text/javascript">

var contributions = $L(); // watchlist of contribution objects, pickled from Indico Contribution objects
var contributionsIndexes = []; //array that maps contribution ids to the index of the contribution in the 'contributions' watchlist
var action = ''; // stores which button has been pressed, in order to know which list of users has to be retrieved

/**
 * Returns a contribution object given its id.
 * The contribution object is obtained from the 'contributions' watchlist.
 * @param {Object} id The id of the contribution.
 */
var getContribution = function (id) {
    return contributions.item(contributionsIndexes[id]);
}

/**
 * Selects all the checkboxes of a given name
 */
var selectAll = function (name) {
    var checkBoxes = document.getElementsByName(name);
    if ( checkBoxes ) { // true if there is at least 1 checkbox
        if ( !checkBoxes.length) { // true if there is only 1 checkbox
            checkBoxes.checked=true
        } else { // there is more than 1 checkbox
            for (i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked=true
            }
        }
    }
}

/**
 * Deselects all the contributions by unticking their checkboxes
 */
var deselectAll = function(name) {
    var checkBoxes = document.getElementsByName(name)
    if ( checkBoxes ) { // true if there is at least 1 checkbox
        if ( !checkBoxes.length) { // true if there is only 1 checkbox
            checkBoxes.checked=false
        } else { // there is more than 1 checkbox
            for (i = 0; i < checkBoxes.length; i++) {
                checkBoxes[i].checked=false
            }
        }
    }
}

/**
 * Builds the 'link' to show and hide the filtering options.
 */
var buildShowHideFiltering = function() {
    var option = new Chooser({
        showFiltering: command(function(){
            $E('filteringTable').dom.style.display = '';
            option.set('hideFiltering');
        }, $T('Show Filtering Criteria')),
        hideFiltering: command(function(){
            $E('filteringTable').dom.style.display = 'none';
            option.set('showFiltering');
        }, $T('Hide Filtering Criteria'))
    });
    option.set('showFiltering');
    
    $E('showHideFiltering').set(Widget.link(option));
}

/**
 * Builds a table row element from a contribution object, pickled from an Indico's Contribution object
 * @param {Object} contribution
 */
var backgroundColorOver = function() {
    IndicoUI.Widgets.Generic.tooltip(this.style.backgroundColor='#ECECEC');
}

var backgroundColorOut = function() {
    IndicoUI.Widgets.Generic.tooltip(this.style.backgroundColor='transparent');
}

var contributionTemplate = function(contribution) {
        
    var row = Html.tr();
    row.dom.onmouseover = backgroundColorOver;
    row.dom.onmouseout = backgroundColorOut;
    // Cell1: checkbox to select this contribution
    var cell1 = Html.td({style:{"textAlign":"center", "width":"0px"}});
    var id = ("cb" + contribution.id);
    var name = ("selectedContributions");
    
    /*
    //creating the checkbox IE way
    if (document.all) {    
    var checkbox = document.createElement('<input name='+name+'>');
    checkbox.type = "checkbox"; 
    checkbox.id = id ;
    }
    //the other browsers
    else {
        var checkbox = Html.checkbox({id: id, name:name});
    }
    cell1.set(checkbox);
    //checkbox.dom.value = contribution.id; // has to be added after constructor because of IE
    */
    var checkbox = Html.input('checkbox', {id: id, name:name});
    checkbox.dom.value = contribution.id;
    cell1.set(checkbox);
    
    row.append(cell1);
    
    // Cell2: contribution id
    var cell2 = Html.td({style:{"textAlign":"center", "width":"0px"}});
    cell2.set(contribution.id)
    row.append(cell2);

    // Cell3: contribution title
    var cell3 = Html.td();
    // Sadly this hack is necessary to get the link since getURL() needs a Contribution object (from Indico, not the local one from Javascript)
    // and contributions are loaded asynchronously...
    linkString = "<%= urlHandlers.UHContributionModifReviewing.getURL() %>" + "?contribId=" + contribution.id + "&confId=<%= Conference.getId()%>"
    var link = Html.a({href: linkString}); 
    link.set(contribution.title);
    cell3.set(link);
    row.append(cell3);

    // Cell4: contribution type
    var cell4 = Html.td({style:{"marginLeft":"5px"}});
    cell4.set(contribution.type)
    row.append(cell4);
    
    // Cell5: contribution track
    var cell5 = Html.td({style:{"marginLeft":"5px"}});
    cell5.set(contribution.track ? contribution.track.title : "")
    row.append(cell5);
    
    // Cell6: contribution session
    var cell6 = Html.td({style:{"marginLeft":"5px"}});
    cell6.set(contribution.session ? contribution.session.title : "")
    row.append(cell6);

    /*
    // Cell7: contribution status
    var cell7 = Html.td();
    
    if (contribution.reviewManager.lastReview.refereeJudgement.isSubmitted) {
        var span = Html.span();
        span.dom.style.color = 'green';
        span.set("Judged" + contribution.reviewManager.lastReview.refereeJudgement.judgement);
        cell7.set(span);
        
    } else {
        var ul = Html.ul();
        ul.dom.style.color = 'red';
        ul.dom.style.listStyleType = 'none';
        ul.dom.style.padding = 0;
        ul.dom.style.marginLeft = '5px';
        
        var li = Html.li();
        li.set("Not judged yet");
        ul.append(li);
        
        statusList = contribution.reviewManager.lastReview.reviewingStatus;
        for (j in statusList) {
            var li = Html.li();
            li.set(statusList[j])
            ul.append(li)
        }
        
        cell7.set(ul);
    }

    row.append(cell7);
    */

    // Cell8: reviewing team assigned to the contribution
    var cell8 = Html.td();
    
    var ul = Html.ul();
    ul.dom.style.listStyleType = 'none';
    ul.dom.style.padding = 0;
    ul.dom.style.marginLeft = '5px';
    
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %> 
    var li1 = Html.li();
    var span1 = Html.span({}, $T('Referee: '))
    var span2 = contribution.reviewManager.referee ?
                    Html.span({id: ("creferee" + contribution.id), style:{"fontWeight":"bolder"}},  contribution.reviewManager.referee.name) :
                    Html.span({id: ("creferee" + contribution.id)},$T('No referee'));
    li1.set(Widget.block([span1,span2]));
    ul.append(li1);
    <% end %>
    
    <% if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1): %>
    var li2 = Html.li();
    var span1 = Html.span({}, $T('Layout reviewer: '))
    var span2 = contribution.reviewManager.editor ?
                    Html.span({id: ("ceditor" + contribution.id), style:{"fontWeight":"bolder"}},  contribution.reviewManager.editor.name) :
                    Html.span({id: ("ceditor" + contribution.id)},$T('No layout reviewer'));
    li2.set(Widget.block([span1,span2]));
    ul.append(li2);
    <% end %>
    
    <% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
    var li3 = Html.li();
    var span = Html.span({id : ("creviewerstitle" + contribution.id)}, $T('Content reviewers: '));
    li3.append(span);
    
    
    var ulReviewers = Html.ul();
    if (contribution.reviewManager.reviewersList.length > 0){
        for (j in contribution.reviewManager.reviewersList) {
            var li = Html.li({id: ("creviewer" + contribution.id + "_" + contribution.reviewManager.reviewersList[j].id), style:{"fontWeight":"bolder"}});
            li.set(contribution.reviewManager.reviewersList[j].name);
            ulReviewers.append(li);
        }
        li3.append(ulReviewers);
    } else {
        var span = Html.span({id: ("creviewer" + contribution.id)},$T('No content reviewers' ));
        li3.append(span);
    }
    ul.append(li3);
    <% end %>
    
    cell8.set(ul);
    row.append(cell8);

    // Cell9: due date of the contribution
    var cell9 = Html.td();
    cell9.set(contribution.reviewManager.lastReview.refereeDueDate)
    row.append(cell9);
    
    return row;
}


/**
 * Updates the display of the contribution row.
 * @param {Object} id The id of the contribution.
 */
var updateContribution = function (id) {
    index = contributionsIndexes[id];
    var c = contributions.item(index);
    contributions.removeAt(index);
    contributions.insert(c, index);
}


/**
 * Returns a list of checkbox values, for a given checkbox name
 * ('name' attribute of an 'input' HTML element)
 * The list only contains the checkboxes who are selected.
 * The first checkbox ('--not specified--' one) is discarded.
 * @param {Object} checkboxName 
 */
var getCheckedBoxes = function(checkboxName) {
    
    var checkBoxes = document.getElementsByName(checkboxName);
    var checkedIds = []
    for (var i=0; i<checkBoxes.length; i++) {
        var cb = checkBoxes[i];
        if (cb.checked && cb.value != "not specified") {
            checkedIds.push(cb.value)
        }
    }
    return checkedIds;
}


/**
 * Returns a list of contribution ids.
 * Only the contributios whose checkbox has been selected are returned.
 */
var getCheckedContributions = function() {
    
    var checkBoxes = document.getElementsByName('selectedContributions');
    var checkedContributions = []
    
    for (var i=0; i<checkBoxes.length; i++) {
        var cb = checkBoxes[i];
        if (cb.checked) {
            checkedContributions.push(cb.id.slice(2))
        }
    }
    return checkedContributions;
}

/**
 * Turns the given user orange for some seconds to indicate that it has changed
 * @param {Object} contributionId The id of the contribution where a user has been assigned
 * @param {Object} role The role that has been assigned
 * @param {Object} reviewerId In case of a reviewerm the reviewerId. Otherwise leave to null.
 */
var colorify = function(contributionId, role, reviewerId) {
    id = "c" + role + contributionId;
    if (reviewerId) {
        id = id + "_" + reviewerId;
    }
    IndicoUI.Effect.highLight(id, 'orange', 2000);
}

/**
 * Among a list of contributions (given as contribution ids),
 * this function unchecks the checboxes of the contributions
 * who don't ahve a refree yet.
 * @param {array} contributions List of contribution ids
 */
var deselectWithoutReferee = function(contributions) {
    for (i in contributions) {
        contributionId = contributions[i];
        contribution = getContribution(contributionId);
        if (contribution.reviewManager.referee == null) {
            $E('cb' + contributionId).dom.checked = false;
        }
    }
}

/**
 * Among a list of contributions (given as contribution ids),
 * this function unchecks the checboxes of the contributions
 * who don't have a reviewer.
 * @param {array} contributions List of contribution ids
 */
var deselectWithoutReviewer = function(contributions) {
    for (i in contributions) {
        contributionId = contributions[i];
        contribution = getContribution(contributionId);
        if (contribution.reviewManager.reviewersList.length == 0) {
            $E('cb' + contributionId).dom.checked = false;
        }
    }
}

/**
 * Checks that all contributions have a Referee.
 * Returns true if all have a referee, false otherwise.
 * If none have a referee, an alert message appear.
 * If some have a referee and others don't, a dialog will appear offering
 * the choice to only apply the assignment to contributions with referee. 
 * @param {Object} contributions
 * @param {Object} order
 * @param {Object} role
 */
var checkAllHaveReferee = function(contributions, order, role) {
    var contributionsWithoutReferee = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.referee == null) {
            contributionsWithoutReferee.push(contributionId)
        }
    }
    if (contributionsWithoutReferee.length == contributions.length) {
        alert($T("None of the contributions you checked have a Referee.") +
            $T("You can only add an editor or a reviewer if the contribution has a referee.")
        );
        return false;
    }
    
    if (contributionsWithoutReferee.length > 0) {
        title =$T('Contributions without referee');    
            
        var popup = new ExclusivePopup(title, function(){popup.close();});
        
        popup.draw = function(){
        
            var span1 = Html.span({}, $T("Some of the contributions you checked do not have a Referee."));
            var span2 = Html.span({}, $T("You can only add an editor or a reviewer if the contribution has a referee.")); 
            var span3 = Html.span({}, $T("Do you want to add that " + role + " only to the contributions with a referee?"));
            var yesButton = Html.button('popUpButton', $T("Yes"));
            yesButton.observeClick(function(){
                deselectWithoutReferee(contributions);
                fetchUsers(order, role);
                popup.close();
            });
                        
             var noButton = Html.button('popUpButton', $T("No"));
            noButton.observeClick(function(){
                popup.close();
            }); 
              var buttons = Widget.inline([yesButton, noButton])
              var all = Widget.lines([span1, span2, span3, buttons])
         return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {height: '130px', width: '420px'}},[all]));  
                };
             popup.open();
          
        return false;
    }
    return true;
}

/**
 * When removing a reviewer from one or more contributions this function takes care for the alert messages.
 * Returns true if there are no warnings, returns false otherwise.
 * If are checked contributions with no reviewers assigned, an alert message appears.
 * If some have a reviewers and others don't, a dialog will appear offering
 * the choice to only apply the assignment to contributions with reviewer. 
 * @param {Object} contributions
 * @param {Object} order
 * @param {Object} role
 */
var removeReviewersAlerts = function(contributions, order, role) {
    contributionsWithoutReviewers = []
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
        if (contribution.reviewManager.reviewersList.length == 0) {
            contributionsWithoutReviewers.push(contributionId)
        }
    } 
    if (contributionsWithoutReviewers.length == contributions.length) {
        alert($T("There is no assigned Reviewer to remove.")
        );
        return false;
    }
    
    if (contributionsWithoutReviewers.length > 0) {
        title =$T('Contributions without reviewer');    
            
        var popup = new ExclusivePopup(title, function(){popup.close();});
        
        popup.draw = function(){
        
            var span1 = Html.span({}, $T("Some of the contributions you checked do not have a Reviewer."));
            var span2 = Html.span({}, $T("Do you want to remove a reviewer only from the contributions that have one?"));
            var yesButton = Html.button('popUpButton', $T("Yes"));
            yesButton.observeClick(function(){
                deselectWithoutReviewer(contributions);
                fetchUsers(order, role);
                popup.close();
            });
                        
             var noButton = Html.button('popUpButton', $T("No"));
             noButton.observeClick(function(){
                popup.close();
            }); 
              var buttons = Widget.inline([yesButton, noButton])
              var all = Widget.lines([span1, span2, buttons])
              return this.ExclusivePopup.prototype.draw.call(this, Html.div({style: {height: '130px', width: '420px'}},[all]));  
                };
             popup.open();
          
        return false;
    }
    
    return true;    
}

/**
 * When removing a refereee from one or more contributions this function checks
 * if there are alredy assigned reviewers or editor, or both 
 * @param {array} contributions List of contribution ids
 */
var removeRefereeAlerts = function(contributions){
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
    }
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor != null) { 
            return false;
        } 
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor == null){
           return false;
        }
    if(contribution.reviewManager.reviewersList.length == 0 && contribution.reviewManager.editor != null) {
            return false;
        }
    
    return true; 
}

/**
 * When removing a refereee from one or more contributions this function takes care for the alert messages.
 * If are checked contributions with alredy assigned reviewers/editor
 * alert message appears that a referee should be assigned
 * @param {array} contributions List of contribution ids
 */    
var removeRefereeAlertsMessage = function(contributions){
    for (i in contributions) {
        contributionId = contributions[i]
        contribution = getContribution(contributionId)
    }
    var warning = $T("You have to assign new referee.")
    var message = $T("nothing")
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor != null) {        
            message = $T("Please note that there are already assigned reviewers and editor." + " " + warning)
            return message;
        } 
    if(contribution.reviewManager.reviewersList.length != 0 && contribution.reviewManager.editor == null){
           message = $T("Please note that there are already assigned reviewers." + " " + warning)
           return message;
        }
    if(contribution.reviewManager.reviewersList.length == 0 && contribution.reviewManager.editor != null) {
           message = $T("Please note that there is already assigned an editor." + " " + warning)
            return message;
        }
    
    return message; 
}
                       
/**
 * Function that is called when a user (referee, editor, reviewer) is clicked.
 * Depending on what has been sotred in the variable 'action', the user will be
 * added as a referee, added as an editor, removed as a reviewer, etc on the checked contributions.
 * @param {Object} user The user that has been clicked.
 */
var userSelected = function(user){
    
    var checkedContributions = getCheckedContributions()

    if (checkedContributions.length > 0) {
        
        var params = {conference: '<%= Conference.getId() %>',contributions: checkedContributions, user: user.id}
        
        switch(action) {
        case 'assign_referee':
            indicoRequest(
                'reviewing.conference.assignReferee',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i];
                            contribution = getContribution(contributionId);
                            contribution.reviewManager.referee = user;
                            updateContribution(contributionId);
                            colorify(contributionId,'referee');
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }
                }
            );
            break;
            
        case 'assign_editor':
            indicoRequest(
                'reviewing.conference.assignEditor',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)
                            contribution.reviewManager.editor = user
                            updateContribution(contributionId)
                            colorify(contributionId,'editor');
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }     
                }
            );
            break;
            
        case 'add_reviewer':
            indicoRequest(
                'reviewing.conference.addReviewer',
                params,
                function(result,error) {
                    if (!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)
                            
                            var present = false;
                            for (j in contribution.reviewManager.reviewersList) {
                                if (contribution.reviewManager.reviewersList[j].id == user.id) {
                                    present = true;
                                    break;
                                }
                            }
                            if (!present) {
                                contribution.reviewManager.reviewersList.push(user)
                            }

                            updateContribution(contributionId);
                            colorify(contributionId,'reviewer', user.id);
                            $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                        }
                    } else {
                        IndicoUtil.errorReport(error);
                    }  
                }
            );
            break;
            
        case 'remove_reviewer':
            indicoRequest(
                'reviewing.conference.removeReviewer',
                params,
                function(result, error) {
                    notinlist2 = [];
                    if(!error) {
                        for (i in checkedContributions) {
                            contributionId = checkedContributions[i]
                            contribution = getContribution(contributionId)
                            
                            notinlist = false;
                            deleted = false;
                            for (j in contribution.reviewManager.reviewersList) {
                                if (contribution.reviewManager.reviewersList[j].id == user.id) {
                                    contribution.reviewManager.reviewersList.splice(j,1);
                                    updateContribution(contributionId);
                                    colorify(contributionId,'reviewerstitle');
                                    $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                                    deleted = true;
                                } else {
                                    notinlist = true;
                                    notinlist2.push(contributionId)
                                    $E('cb' + contributionId).dom.checked = false;
                                   
                                }
                            }                   
                        }
                   } else {
                        IndicoUtil.errorReport(error);
                   } 
                }
            );
            break;
            
        default:
            break;
        }
                
    }
}



/**
 * Requests the list of contribution from the server,
 * given the filtering parameters.
 */
var fetchContributions = function() {
    
    contributions.clear();
    contributionsIndexes = []
    indicoRequest('event.contributions.list',
        {
            conference: '<%= Conference.getId() %>',
            typeShowNoValue : $E('typeShowNoValue').dom.checked,
            trackShowNoValue : $E('trackShowNoValue').dom.checked,
            sessionShowNoValue : $E('sessionShowNoValue').dom.checked,
            selTypes : getCheckedBoxes('selTypes'),
            selTracks : getCheckedBoxes('selTracks'),
            selSessions : getCheckedBoxes('selSessions'),
            <% if not IsOnlyReferee: %>
            showWithReferee: $E('showWithReferee').dom.checked,
            <% end %>
            showWithEditor: $E('showWithEditor').dom.checked,
            showWithReviewer: $E('showWithReviewer').dom.checked
        },
        function(result, error){
            if (!error) {
                for (i in result) {
                    c = result[i]
                    contributions.append(c);
                    contributionsIndexes[c.id] = i;
                }
            } else {
                IndicoUtil.errorReport(error);
            }
        }
    )
}

/**
 * Retrieves a list of users from the server.
 * @param {string} order The action that will be taken on the users: 'assign', 'remove'.
 * @param {string} role The role of the users: 'referee', 'editor', 'reviewer'.
 */
var fetchUsers = function(order, role) {
    
    var checkedContributions = getCheckedContributions();
    if (checkedContributions.length == 0) {
        alert($T("Please select at least 1 contribution"));
        return;
    }
    
    if ((order == 'assign' && role == 'editor') || (order == 'add' && role == 'reviewer')) {
        if (!checkAllHaveReferee(checkedContributions, order, role)) {
            return;
        } 
   }
   
   if (order == 'remove' && role == 'reviewer')  {
        if (!removeReviewersAlerts(checkedContributions, order, role)) {
            return;
        } 
   }
    
    indicoRequest(
        'reviewing.conference.userCompetencesList',
        {conference: '<%= Conference.getId() %>', role: role},
        function(result,error) {
            if (!error) {
                
                action = order + '_' + role;
                
                var title = '';
                if (role == 'editor') {
                    title = $T('Click on a user name to ') + order + $T(' an layout reviewer:');
                } 
                if (role == 'reviewer') {
                    title = $T('Click on a user name to ') + order + ' a ' + $T('content reviewer:');
                } else {
                    title = $T('Click on a user name to ') + order + ' a ' + role + ':';
                } 
                
                var popup = new ExclusivePopup(title, function(){popup.close();});
                
                popup.draw = function(){
	                    var users = $L(); 
	                    var userTemplate = function(user) {
	                        var li = Html.li();
	                        var userName = Widget.link(command(function(){
	                            userSelected(user);
	                            var killProgress = IndicoUI.Dialogs.Util.progress()
	                            popup.close();
	                            killProgress();
	                        }, user.name));
	                    
	                    
	                    var userCompetences = Html.span({style:{marginLeft:'5px'}},
                            user.competences.length == 0 ? $T('(no competences defined)') : $T('(competences: ') + user.competences.join(', ') + ')'
                        );
                        
                        li.set(Widget.inline([userName, userCompetences]));
                        return li;
                    }    
	                
                        var userList = Html.ul();
                        bind.element(userList, users, userTemplate);
                        
                        for (i in result) {
                        users.append(result[i]);
                        }                        
                         
                        var cancelButton = Html.button({style:{marginLeft:pixels(5)}}, $T("Cancel"));
                          cancelButton.observeClick(function(){
                          popup.close();
                           });
                       
                       var span1 = Html.span({}, "");
                       var message = '';
                       if(role == 'referee' && order == 'assign' && !removeRefereeAlerts(checkedContributions)) {
                            span1 = Html.span({}, removeRefereeAlertsMessage(checkedContributions));
                       }   
                       if(role == 'reviewer' && order == 'remove') {
                            if (checkedContributions.length == 1){
                                    message = $T("The Reviewer you choose will be removed only from the contribution that is assigned to him/her.") 
                                } else {
                                    message = $T("The Reviewer you choose will be removed only from the contributions that are assigned to him/her.")
                                }
                            span1 = Html.span({}, message);
                       }    
                        return this.ExclusivePopup.prototype.draw.call(this, Widget.block([span1, userList, cancelButton]));  
                };
             popup.open();
              
            } else {
                IndicoUtil.errorReport(error);
            }
        }
    );
}

/**
 * Removes the referee, the editor, or all the reviewers from the contributions that are selected.
 * @param {Object} role 'referee', 'editor', 'allReviewers'
 */
var removeUser = function(role) {
    
    var checkedContributions = getCheckedContributions();
    if (checkedContributions.length == 0) {
        alert($T("Please select at least 1 contribution"));
        return;
    }
   
    var params = {conference: '<%= Conference.getId() %>',contributions: checkedContributions}
    
    switch(role) {
    case 'referee':
        indicoRequest(
            'reviewing.conference.removeReferee',
            params,
            function(result,error) {
                if (!error) {
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        contribution.reviewManager.referee = null;
                        updateContribution(contributionId);
                        colorify(contributionId, 'referee')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                                                
                    }
                    if(!removeRefereeAlerts(checkedContributions)){
                      fetchUsers('assign', 'referee')
                    } 
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
        break;
    case 'editor':
        indicoRequest(
            'reviewing.conference.removeEditor',
            params,
            function(result,error) {
                if (!error) {
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        contribution.reviewManager.editor = null;
                        updateContribution(contributionId);
                        colorify(contributionId, 'editor')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
        break;
    case 'allReviewers':
        indicoRequest(
            'reviewing.conference.removeAllReviewers',
            params,
            function(result,error) {
                if (!error) {
                    for (i in checkedContributions) {
                        contributionId = checkedContributions[i];
                        contribution = getContribution(contributionId);
                        if (!removeReviewersAlerts(checkedContributions, role)) {
                                return;
                        } 
                        contribution.reviewManager.reviewersList = [];
                        updateContribution(contributionId);
                        colorify(contributionId, 'reviewer')
                        $E('cb' + contributionId).dom.checked = true; //updateContribution will build a row with an unchecked checkbox
                    }
                } else {
                    IndicoUtil.errorReport(error);
                }
            }
        );
    default:
        break;
    }
}

// Code to be executed on page load

buildShowHideFiltering();
$E('filteringTable').dom.style.display = 'none';

bind.element($E("tablebody"), contributions, contributionTemplate);

$E('applyFilter').observeClick(fetchContributions);

<% if not IsOnlyReferee and not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
$E('assignRefereeButton_top').observeClick(function(){ fetchUsers('assign', 'referee'); });
$E('assignRefereeButton_bottom').observeClick(function(){ fetchUsers('assign', 'referee'); });
$E('removeRefereeButton_top').observeClick(function(){ removeUser('referee') });
$E('removeRefereeButton_bottom').observeClick(function(){ removeUser('referee') });
<% end %>

<% if not (ConfReview.getChoice() == 2 or ConfReview.getChoice() == 1): %>
$E('assignEditorButton_top').observeClick(function(){ fetchUsers('assign', 'editor'); });
$E('assignEditorButton_bottom').observeClick(function(){ fetchUsers('assign', 'editor'); });
$E('removeEditorButton_top').observeClick(function(){ removeUser('editor') });
$E('removeEditorButton_bottom').observeClick(function(){ removeUser('editor') });
<% end %>

<% if not (ConfReview.getChoice() == 3 or ConfReview.getChoice() == 1): %>
$E('addReviewerButton_top').observeClick(function(){ fetchUsers('add', 'reviewer'); });
$E('addReviewerButton_bottom').observeClick(function(){ fetchUsers('add', 'reviewer'); });
$E('removeReviewerButton_top').observeClick(function(){ fetchUsers('remove', 'reviewer'); });
$E('removeReviewerButton_bottom').observeClick(function(){ fetchUsers('remove', 'reviewer'); });
$E('removeAllReviewersButton_top').observeClick(function(){ removeUser('allReviewers') });
$E('removeAllReviewersButton_bottom').observeClick(function(){ removeUser('allReviewers') });
<% end %>


fetchContributions();
    
</script>
<% end %>
<% end %>
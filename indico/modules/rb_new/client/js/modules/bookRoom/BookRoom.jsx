/* This file is part of Indico.
 * Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

import {connect} from 'react-redux';
import {stateToQueryString} from 'redux-router-querystring';
import moment from 'moment';
import PropTypes from 'prop-types';
import React from 'react';
import _ from 'lodash';
import {Route} from 'react-router-dom';
import {Button, Card, Dimmer, Grid, Header, Icon, Label, Loader, Message, Popup, Sticky} from 'semantic-ui-react';
import LazyScroll from 'redux-lazy-scroll';

import {Slot, toClasses} from 'indico/react/util';
import {PluralTranslate, Translate, Singular, Param, Plural} from 'indico/react/i18n';
import mapControllerFactory from '../../containers/MapController';
import filterBarFactory from '../../containers/FilterBar';
import searchBoxFactory from '../../containers/SearchBar';
import Room from '../../containers/Room';
import BookingFilterBar from './BookingFilterBar';
import BookingTimeline from './BookingTimeline';
import BookRoomModal from './BookRoomModal';
import SearchResultCount from './SearchResultCount';
import roomDetailsModalFactory from '../../components/modals/RoomDetailsModal';
import {roomPreloader, pushStateMergeProps} from '../../util';
import {queryString as qsFilterRules} from '../../serializers/filters';
import {rules as qsBookRoomRules} from './queryString';

import * as bookRoomActions from './actions';
import * as globalActions from '../../actions';
import * as globalSelectors from '../../selectors';
import {actions as roomsActions, selectors as roomsSelectors} from '../../common/rooms';

import './BookRoom.module.scss';


const FilterBar = filterBarFactory('bookRoom', BookingFilterBar);
const SearchBar = searchBoxFactory('bookRoom');
const MapController = mapControllerFactory('bookRoom');
const RoomDetailsModal = roomDetailsModalFactory('bookRoom');


class BookRoom extends React.Component {
    static propTypes = {
        setFilterParameter: PropTypes.func.isRequired,
        clearTextFilter: PropTypes.func.isRequired,
        rooms: PropTypes.shape({
            list: PropTypes.array,
            matching: PropTypes.number,
            isFetching: PropTypes.bool,
            isLoadingMore: PropTypes.bool
        }).isRequired,
        isInitializing: PropTypes.bool.isRequired,
        fetchRooms: PropTypes.func.isRequired,
        filters: PropTypes.object.isRequired,
        timeline: PropTypes.object.isRequired,
        clearRoomList: PropTypes.func.isRequired,
        roomDetailsFetching: PropTypes.bool.isRequired,
        fetchRoomDetails: PropTypes.func.isRequired,
        resetBookingAvailability: PropTypes.func.isRequired,
        suggestions: PropTypes.object.isRequired,
        pushState: PropTypes.func.isRequired,
        toggleTimelineView: PropTypes.func.isRequired,
        showMap: PropTypes.bool.isRequired
    };

    constructor(props) {
        super(props);
        this.contextRef = React.createRef();
    }

    state = {};

    componentDidMount() {
        const {fetchRooms} = this.props;
        fetchRooms();
    }

    componentWillUnmount() {
        const {clearTextFilter, clearRoomList} = this.props;
        clearTextFilter();
        clearRoomList();
    }

    renderRoom = (room) => {
        const {id} = room;
        const {pushState} = this.props;

        const bookingModalBtn = (
            <Button positive icon="check" circular onClick={() => {
                // open confirm dialog, keep same filtering parameters
                pushState(`/book/${id}/confirm`, true);
            }} />
        );
        const showDetailsBtn = (
            <Button primary icon="search" circular onClick={() => {
                pushState(`/book/${id}/details`, true);
            }} />
        );
        return (
            <Room key={room.id} room={room} showFavoriteButton>
                <Slot name="actions">
                    <Popup trigger={bookingModalBtn} content={Translate.string('Book room')} position="top center" hideOnScroll />
                    <Popup trigger={showDetailsBtn} content={Translate.string('Room details')} position="top center" hideOnScroll />
                </Slot>
            </Room>
        );
    };

    renderMainContent = () => {
        const {timelineRef} = this.state;
        const {
            fetchRooms,
            roomDetailsFetching,
            rooms: {
                list, matching, total, isFetching, isLoadingMore
            },
            timeline: {
                isVisible
            }
        } = this.props;
        const filterBar = <FilterBar />;
        const searchBar = <SearchBar onConfirm={fetchRooms} onTextChange={fetchRooms} />;
        const showResults = !isFetching || isLoadingMore;

        if (!isVisible) {
            return (
                <>
                    <div className="ui" styleName="available-room-list" ref={this.contextRef}>
                        <Sticky context={this.contextRef.current} className="sticky-filters">
                            <Grid>
                                <Grid.Column width={13}>
                                    {filterBar}
                                </Grid.Column>
                                {this.renderViewSwitch()}
                            </Grid>
                            {searchBar}
                        </Sticky>
                        <SearchResultCount matching={matching} total={total} isFetching={isFetching} />
                        <LazyScroll hasMore={matching > list.length} loadMore={() => fetchRooms(true)}
                                    isFetching={isFetching}>
                            {showResults && (
                                <Card.Group stackable>
                                    {list.map(this.renderRoom)}
                                </Card.Group>
                            )}
                            <Loader active={isFetching} inline="centered" styleName="rooms-loader" />
                        </LazyScroll>
                        {showResults && this.renderSuggestions()}
                    </div>
                    <Dimmer.Dimmable>
                        <Dimmer active={roomDetailsFetching} page>
                            <Loader />
                        </Dimmer>
                    </Dimmer.Dimmable>
                </>
            );
        } else {
            return (
                <div ref={(ref) => this.handleContextRef(ref, 'timelineRef')}>
                    <Sticky context={timelineRef} className="sticky-filters">
                        <Grid>
                            <Grid.Column width={13}>
                                {filterBar}
                            </Grid.Column>
                            {this.renderViewSwitch()}
                        </Grid>
                        <Grid.Row>
                            {searchBar}
                        </Grid.Row>
                    </Sticky>
                    <BookingTimeline minHour={6} maxHour={22} />
                </div>
            );
        }
    };

    renderSuggestions = () => {
        const {suggestions} = this.props;

        if (!suggestions.list || !suggestions.list.length) {
            return;
        }

        return (
            <>
                <Header as="h2">
                    <Translate>Rooms that you might be interested in</Translate>
                </Header>
                <Card.Group styleName="suggestions" stackable>
                    {suggestions.list.map((suggestion) => this.renderSuggestion(suggestion))}
                </Card.Group>
            </>
        );
    };

    renderSuggestion = ({room, suggestions}) => {
        return (
            <Room key={room.id} room={room}>
                <Slot>
                    <Grid centered styleName="suggestion" columns={3}>
                        <Grid.Column verticalAlign="middle" width={14}>
                            {this.renderSuggestionText(room, suggestions)}
                        </Grid.Column>
                    </Grid>
                </Slot>
            </Room>
        );
    };

    suggestionTooltip = (element) => (
        <Popup trigger={element} content={Translate.string('The filtering criteria will be adjusted accordingly')} />
    );

    renderSuggestionText = (room, {time, duration, skip}) => {
        const {pushState} = this.props;
        return (
            <>
                {time && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('time', time)}
                             warning compact>
                        <Message.Header>
                            <Icon name="clock" />
                            <PluralTranslate count={time}>
                                <Singular>
                                    One minute <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Singular>
                                <Plural>
                                    <Param name="count" value={Math.abs(time)} /> minutes{' '}
                                    <Param name="modifier" value={time < 0 ? 'earlier' : 'later'} />
                                </Plural>
                            </PluralTranslate>
                        </Message.Header>
                    </Message>
                )}
                {duration && time && (
                    <div>
                        <Label color="brown" circular>{Translate.string('or')}</Label>
                    </div>
                )}
                {duration && this.suggestionTooltip(
                    <Message styleName="suggestion-text" size="mini" onClick={() => this.updateFilters('duration', duration)}
                             warning compact>
                        <Message.Header>
                            <Icon name="hourglass full" /> {PluralTranslate.string('One minute shorter', '{duration} minutes shorter', duration, {duration})}
                        </Message.Header>
                    </Message>
                )}
                {skip && (
                    <Message styleName="suggestion-text" size="mini" onClick={() => {
                        pushState(`/book/${room.id}/confirm`, true);
                    }} warning compact>
                        <Message.Header>
                            <Icon name="calendar times" /> {PluralTranslate.string('Skip one day', 'Skip {skip} days', skip, {skip})}
                        </Message.Header>
                    </Message>
                )}
            </>
        );
    };

    updateFilters = (filter, value) => {
        const {setFilterParameter} = this.props;
        let {filters: {timeSlot: {startTime, endTime}}} = this.props;

        if (filter === 'duration') {
            endTime = moment(endTime, 'HH:mm').subtract(value, 'minutes').format('HH:mm');
        } else if (filter === 'time') {
            startTime = moment(startTime, 'HH:mm').add(value, 'minutes').format('HH:mm');
            endTime = moment(endTime, 'HH:mm').add(value, 'minutes').format('HH:mm');
        }
        setFilterParameter('timeSlot', {startTime, endTime});
    };

    renderViewSwitch() {
        const {switcherRef} = this.state;
        const {timeline: {availability, isVisible}} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);
        const hasConflicts = timelineDataAvailable && Object.values(availability).some((data) => {
            return !_.isEmpty(data.conflicts);
        });
        const classes = toClasses({active: isVisible, disabled: !timelineDataAvailable});

        const listBtn = (
            <Button icon={<Icon name="grid layout" styleName="switcher-icon" />}
                    className={toClasses({active: !isVisible})}
                    onClick={this.switchToRoomList} circular />
        );
        const timelineBtn = (
            <Button icon={<Icon name="calendar outline" styleName="switcher-icon" disabled={!timelineDataAvailable} />}
                    className={classes} circular />
        );
        return (
            <Grid.Column width={3} styleName="view-icons" textAlign="right" verticalAlign="middle">
                <div ref={(ref) => this.handleContextRef(ref, 'switcherRef')} styleName="view-icons-context">
                    <Sticky context={switcherRef} offset={30}>
                        <span styleName="icons-wrapper">
                            {isVisible
                                ? <Popup trigger={listBtn} content={Translate.string('List view')} />
                                : listBtn
                            }
                            <Icon.Group onClick={this.switchToTimeline}>
                                {!isVisible
                                    ? <Popup trigger={timelineBtn} content={Translate.string('Timeline view')} />
                                    : timelineBtn
                                }
                                {hasConflicts && (
                                    <Icon name="exclamation triangle" styleName="conflicts-icon" color="red" corner />
                                )}
                            </Icon.Group>
                        </span>
                    </Sticky>
                </div>
            </Grid.Column>
        );
    }

    switchToRoomList = () => {
        const {toggleTimelineView} = this.props;
        toggleTimelineView(false);
        this.setState({timelineRef: null});
    };

    switchToTimeline = () => {
        const {timeline: {availability}, toggleTimelineView} = this.props;
        const timelineDataAvailable = !_.isEmpty(availability);
        if (timelineDataAvailable) {
            toggleTimelineView(true);
        }
    };

    handleContextRef = (ref, kind) => {
        if (kind in this.state) {
            const {[kind]: context} = this.state;
            if (context !== null) {
                return;
            }
        }
        this.setState({[kind]: ref});
    };

    closeBookingModal = () => {
        const {resetBookingAvailability} = this.props;
        resetBookingAvailability();
        this.closeModal();
    };

    closeModal = () => {
        const {pushState} = this.props;
        pushState(`/book`, true);
    };

    render() {
        const {fetchRoomDetails, showMap, isInitializing} = this.props;
        return (
            <Grid columns={2}>
                <Grid.Column width={showMap ? 11 : 16}>
                    {this.renderMainContent()}
                </Grid.Column>
                {showMap && (
                    <Grid.Column width={5}>
                        <MapController />
                    </Grid.Column>
                )}
                {!isInitializing && (
                    <>
                        <Route exact path="/book/:roomId/confirm" render={roomPreloader((roomId) => (
                            <BookRoomModal open roomId={roomId} onClose={this.closeBookingModal} />
                        ), fetchRoomDetails)} />
                        <Route exact path="/book/:roomId/details" render={roomPreloader((roomId) => (
                            <RoomDetailsModal roomId={roomId} onClose={this.closeModal} />
                        ), fetchRoomDetails)} />
                    </>
                )}
            </Grid>
        );
    }
}


const mapStateToProps = (state) => {
    return {
        ...state.bookRoom,
        roomDetailsFetching: roomsSelectors.isFetchingDetails(state),
        isInitializing: globalSelectors.isInitializing(state),
        queryString: stateToQueryString(state.bookRoom, qsFilterRules, qsBookRoomRules),
        showMap: globalSelectors.isMapEnabled(state),
    };
};

const mapDispatchToProps = dispatch => ({
    clearRoomList() {
        dispatch(globalActions.updateRooms('bookRoom', [], 0, true));
    },
    clearTextFilter() {
        dispatch(globalActions.setFilterParameter('bookRoom', 'text', null));
    },
    fetchRooms(loadMore = false) {
        dispatch(bookRoomActions.searchRooms(loadMore));
        dispatch(globalActions.fetchMapRooms('bookRoom'));
    },
    fetchRoomDetails(id) {
        dispatch(roomsActions.fetchDetails(id));
    },
    resetBookingAvailability() {
        dispatch(bookRoomActions.resetBookingAvailability());
    },
    setFilterParameter(param, value) {
        dispatch(globalActions.setFilterParameter('bookRoom', param, value));
        dispatch(bookRoomActions.searchRooms());
        dispatch(globalActions.fetchMapRooms('bookRoom'));
    },
    toggleTimelineView: (isVisible) => {
        dispatch(bookRoomActions.toggleTimelineView(isVisible));
    },
    dispatch
});

export default connect(
    mapStateToProps,
    mapDispatchToProps,
    pushStateMergeProps
)(BookRoom);

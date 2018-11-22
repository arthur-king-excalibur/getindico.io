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

import React from 'react';
import PropTypes from 'prop-types';
import {bindActionCreators} from 'redux';
import {connect} from 'react-redux';
import {Field} from 'react-final-form';
import {Icon, List, Popup} from 'semantic-ui-react';
import {formatters, ReduxDropdownField, ReduxFormField} from 'indico/react/forms';
import {Param, Plural, PluralTranslate, Singular, Translate} from 'indico/react/i18n';
import * as adminActions from './actions';
import * as adminSelectors from './selectors';
import EditableList from './EditableList';

import './EditableList.module.scss';


class EquipmentTypeList extends React.PureComponent {
    static propTypes = {
        isFetching: PropTypes.bool.isRequired,
        equipmentTypes: PropTypes.array.isRequired,
        features: PropTypes.array.isRequired,
        actions: PropTypes.exact({
            deleteEquipmentType: PropTypes.func.isRequired,
            updateEquipmentType: PropTypes.func.isRequired,
            createEquipmentType: PropTypes.func.isRequired,
        }).isRequired,
    };

    renderItem = ({name, features, numRooms}) => (
        <List.Content styleName="info">
            <List.Header>
                <span styleName="name">{name}</span>
                {features.map(feat => (
                    <Popup key={feat.name}
                           trigger={<Icon name={feat.icon || 'cog'} color="blue" />}>
                        <Translate>
                            This equipment type provides the
                            {' '}
                            <Param name="name" wrapper={<strong />} value={feat.title} /> feature.
                        </Translate>
                    </Popup>
                ))}
            </List.Header>
            <List.Description>
                {!numRooms ? (
                    <Translate>Currently unused</Translate>
                ) : (
                    <PluralTranslate count={numRooms}>
                        <Singular>
                            Available in <Param name="count" wrapper={<strong />}>1</Param> room
                        </Singular>
                        <Plural>
                            Available in
                            {' '}
                            <Param name="count" wrapper={<strong />} value={numRooms} />
                            {' '}
                            rooms
                        </Plural>
                    </PluralTranslate>
                )}
            </List.Description>
        </List.Content>
    );

    renderForm = fprops => {
        const {features} = this.props;

        const featureOptions = features.map(feat => ({
            key: feat.name,
            value: feat.name,
            text: feat.title,
            icon: feat.icon,
        }));

        return (
            <>
                <Field name="name" component={ReduxFormField} as="input"
                       format={formatters.trim} formatOnBlur
                       label={Translate.string('Name')}
                       disabled={fprops.submitting}
                       autoFocus />
                {!!featureOptions.length && (
                    <Field name="features" component={ReduxDropdownField}
                           multiple selection closeOnChange
                           options={featureOptions}
                           label={Translate.string('Features')}
                           disabled={fprops.submitting} />
                )}
            </>
        );
    };

    renderDeleteMessage = ({name, numRooms}) => (
        <>
            <Translate>
                Are you sure you want to delete the equipment type
                {' '}
                <Param name="name" wrapper={<strong />} value={name} />?
            </Translate>
            {numRooms > 0 && (
                <>
                    <br />
                    <PluralTranslate count={numRooms}>
                        <Singular>
                            It is currently used by <Param name="count" wrapper={<strong />}>1</Param> room.
                        </Singular>
                        <Plural>
                            It is currently used by
                            {' '}
                            <Param name="count" wrapper={<strong />} value={numRooms} /> rooms.
                        </Plural>
                    </PluralTranslate>
                </>
            )}
        </>
    );

    render() {
        const {
            isFetching, equipmentTypes,
            actions: {createEquipmentType, updateEquipmentType, deleteEquipmentType},
        } = this.props;

        return (
            <EditableList title={Translate.string('Equipment types')}
                          addModalTitle={Translate.string('Add equipment type')}
                          isFetching={isFetching}
                          items={equipmentTypes}
                          renderItem={this.renderItem}
                          renderAddForm={this.renderForm}
                          renderEditForm={this.renderForm}
                          renderDeleteMessage={this.renderDeleteMessage}
                          initialAddValues={{name: '', features: []}}
                          initialEditValues={item => ({name: item.name, features: item.features.map(x => x.name)})}
                          onCreate={createEquipmentType}
                          onUpdate={updateEquipmentType}
                          onDelete={deleteEquipmentType} />
        );
    }
}


export default connect(
    state => ({
        isFetching: adminSelectors.isFetchingFeaturesOrEquipmentTypes(state),
        equipmentTypes: adminSelectors.getEquipmentTypes(state),
        features: adminSelectors.getFeatures(state),
    }),
    dispatch => ({
        actions: bindActionCreators({
            deleteEquipmentType: ({id}) => adminActions.deleteEquipmentType(id),
            updateEquipmentType: ({id}, data) => adminActions.updateEquipmentType(id, data),
            createEquipmentType: adminActions.createEquipmentType,
        }, dispatch),
    })
)(EquipmentTypeList);

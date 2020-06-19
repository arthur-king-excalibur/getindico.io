// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.
import menuEntriesURL from 'indico-url:event_editing.api_menu_entries';

import React from 'react';
import PropTypes from 'prop-types';
import {Header} from 'semantic-ui-react';
import {useIndicoAxios} from 'indico/react/hooks';

import MenuBar from './MenuBar';
import Footer from './Footer';

import './EditingView.module.scss';

export default function EditingView({eventId, eventTitle, editableType, children}) {
  const {data, lastData} = useIndicoAxios({
    url: menuEntriesURL({confId: eventId}),
    trigger: eventId,
  });

  const menuItems = data || lastData;
  if (!menuItems) {
    return null;
  }

  return (
    <div styleName="editing-view">
      <MenuBar
        eventId={eventId}
        eventTitle={eventTitle}
        menuItems={menuItems}
        editableType={editableType}
      />
      <div styleName="contents">
        <div styleName="timeline">
          <Header as="h2" styleName="header">
            {eventTitle}
          </Header>
          {children}
        </div>
        <Footer />
      </div>
    </div>
  );
}

EditingView.propTypes = {
  eventId: PropTypes.number.isRequired,
  eventTitle: PropTypes.string.isRequired,
  editableType: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
};

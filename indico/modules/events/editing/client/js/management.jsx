// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React from 'react';
import ReactDOM from 'react-dom';

import EditingManagement from './components/EditingManagement';

document.addEventListener('DOMContentLoaded', async () => {
  const editingManagementContainer = document.querySelector('#editing-management');
  if (!editingManagementContainer) {
    return;
  }
  const eventId = parseInt(editingManagementContainer.dataset.eventId, 10);
  ReactDOM.render(<EditingManagement eventId={eventId} />, editingManagementContainer);
});

// This file is part of Indico.
// Copyright (C) 2002 - 2020 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import uploadURL from 'indico-url:event_editing.api_upload';

import React from 'react';
import {useDispatch, useSelector} from 'react-redux';
import PropTypes from 'prop-types';
import {Form as FinalForm} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import {reviewEditable} from '../../../actions';
import * as selectors from '../../../selectors';
import {EditingReviewAction} from '../../../models';
import {FinalFileManager} from '../../FileManager';
import {getFiles} from '../../FileManager/selectors';
import {mapFileTypes} from '../../FileManager/util';
import FinalTagInput from './TagInput';

import './JudgmentBox.module.scss';

export default function UpdateFilesForm({setLoading}) {
  const {fileTypes} = useSelector(selectors.getStaticData);
  const lastRevision = useSelector(selectors.getLastRevision);
  const staticData = useSelector(selectors.getStaticData);
  const {eventId, contributionId, editableType} = staticData;
  const dispatch = useDispatch();

  const files = getFiles({fileTypes: mapFileTypes(fileTypes, lastRevision.files)});

  const submitReview = async formData => {
    setLoading(true);
    const rv = await dispatch(
      reviewEditable(lastRevision, {
        ...formData,
        action: EditingReviewAction.update,
      })
    );
    if (rv.error) {
      setLoading(false);
      return rv.error;
    }
  };

  return (
    <FinalForm
      initialValues={{comment: '', files, tags: lastRevision.tags}}
      subscription={{}}
      onSubmit={submitReview}
    >
      {({handleSubmit}) => (
        <>
          <Form id="judgment-form" onSubmit={handleSubmit}>
            <FinalFileManager
              name="files"
              fileTypes={fileTypes}
              files={lastRevision.files}
              uploadURL={uploadURL({
                confId: eventId,
                contrib_id: contributionId,
                type: editableType,
              })}
            />
            <FinalTextArea
              name="comment"
              placeholder={Translate.string('Leave a comment...')}
              hideValidationError
              autoFocus
            />
            <FinalTagInput name="tags" options={staticData.tags} />
          </Form>
          <div styleName="judgment-submit-button">
            <FinalSubmitButton form="judgment-form" label={Translate.string('Confirm')} />
          </div>
        </>
      )}
    </FinalForm>
  );
}

UpdateFilesForm.propTypes = {
  setLoading: PropTypes.func.isRequired,
};

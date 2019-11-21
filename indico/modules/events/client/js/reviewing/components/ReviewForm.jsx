// This file is part of Indico.
// Copyright (C) 2002 - 2019 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import React, {useState} from 'react';
import {Form as FinalForm} from 'react-final-form';
import {Button, Dropdown, Form} from 'semantic-ui-react';

import {FinalDropdown, FinalSubmitButton, FinalTextArea} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

import JudgmentModal from './JudgmentModal';
import UserAvatar from './UserAvatar';

import './ReviewForm.module.scss';

const visibilityOptions = [
  {
    value: 'editors',
    text: Translate.string('Visible only to editors'),
  },
  {
    value: 'authors',
    text: Translate.string('Visible to editors and authors'),
  },
];

const judgmentOptions = [
  {
    value: 'accept',
    text: Translate.string('Accept'),
  },
  {
    value: 'reject',
    text: Translate.string('Reject'),
  },
  {
    value: 'update',
    text: Translate.string('Make changes'),
  },
  {
    value: 'request_update',
    text: Translate.string('Request changes'),
  },
];

export default function ReviewForm() {
  const currentUser = {
    fullName: Indico.User.full_name,
    avatarBgColor: Indico.User.avatar_bg_color,
  };

  const [commentFormVisible, setCommentFormVisible] = useState(false);
  const [judgmentModalType, setJudgmentModalType] = useState(null);
  const onCommentClickHandler = () => {
    if (!commentFormVisible) {
      setCommentFormVisible(true);
    }
  };

  return (
    <>
      <div className="i-timeline-item review-timeline-input">
        <UserAvatar user={currentUser} />
        <div className="i-timeline-item-box footer-only header-indicator-left">
          <div className="i-box-footer" style={{overflow: 'visible'}}>
            <div className="flexrow">
              <div className="f-self-stretch">
                <FinalForm
                  onSubmit={() => {}}
                  initialValues={{comment: '', visibility: 'editors'}}
                  subscription={{submitting: true}}
                >
                  {fprops => (
                    <Form onSubmit={fprops.handleSubmit}>
                      <FinalTextArea
                        onFocus={onCommentClickHandler}
                        name="comment"
                        rows={commentFormVisible ? 3 : 1}
                        placeholder={Translate.string('Leave a comment...')}
                        style={{resize: commentFormVisible ? 'vertical' : 'none'}}
                        hideValidationError
                        required
                      />
                      {commentFormVisible && (
                        <>
                          <FinalDropdown
                            name="visibility"
                            options={visibilityOptions}
                            width={8}
                            selection
                            required
                          />
                          <Form.Group inline>
                            <FinalSubmitButton label={Translate.string('Comment')} />
                            <Button
                              disabled={fprops.submitting}
                              content={Translate.string('Cancel')}
                              onClick={() => {
                                setCommentFormVisible(false);
                                fprops.form.reset();
                              }}
                            />
                          </Form.Group>
                        </>
                      )}
                    </Form>
                  )}
                </FinalForm>
              </div>
              {!commentFormVisible && (
                <div className="review-trigger flexrow">
                  <span className="comment-or-review">
                    <Translate>or</Translate>
                  </span>
                  <Dropdown
                    className="judgment-btn"
                    text={Translate.string('Judge')}
                    options={judgmentOptions}
                    direction="left"
                    value={null}
                    selectOnNavigation={false}
                    onChange={(_, {value}) => {
                      setJudgmentModalType(value);
                    }}
                    button
                    floating
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
      {/* TODO: open the right dialog based on the selected action */}
      {judgmentModalType && <JudgmentModal onClose={() => setJudgmentModalType(null)} />}
    </>
  );
}

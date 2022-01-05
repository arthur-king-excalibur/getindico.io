// This file is part of Indico.
// Copyright (C) 2002 - 2022 CERN
//
// Indico is free software; you can redistribute it and/or
// modify it under the terms of the MIT License; see the
// LICENSE file for more details.

import createDecorator from 'final-form-calculate';
import PropTypes from 'prop-types';
import TimePicker from 'rc-time-picker';
import React, {useState} from 'react';
import {Field} from 'react-final-form';
import {Form} from 'semantic-ui-react';

import {SingleDatePicker} from 'indico/react/components';
import {FinalDropdown, parsers as p} from 'indico/react/forms';
import {Translate} from 'indico/react/i18n';

export default function DateInput({htmlName, id, disabled, dateFormat, timeFormat}) {
  const [date, setDate] = useState(null);
  const [time, setTime] = useState(null);
  const friendlyDateFormat = dateFormat.replace(
    /%([HMdmY])/g,
    (match, c) => ({H: 'HH', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c])
  );

  if (dateFormat.includes('%d')) {
    return (
      <>
        <SingleDatePicker
          id={`regform-datepicker-${id}`}
          date={date}
          onDateChange={setDate}
          placeholder={friendlyDateFormat}
          displayFormat={friendlyDateFormat}
          disabled={disabled}
          isOutsideRange={() => false}
          enableOutsideDays
          noBorder
          small
        />
        {timeFormat && (
          <TimePicker
            id={`regform-timepicker-${id}`}
            showSecond={false}
            value={time}
            focusOnOpen
            onChange={setTime}
            use12Hours={timeFormat === '12h'}
            allowEmpty={false}
            placeholder={timeFormat === '12h' ? '--:-- am/pm' : '--:--'}
            disabled={disabled}
            getPopupContainer={node => node}
          />
        )}
      </>
    );
  } else {
    return (
      <input type="text" name={htmlName} placeholder={friendlyDateFormat} disabled={disabled} />
    );
  }
}

DateInput.propTypes = {
  htmlName: PropTypes.string.isRequired,
  id: PropTypes.number.isRequired,
  disabled: PropTypes.bool,
  dateFormat: PropTypes.oneOf([
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ]).isRequired,
  timeFormat: PropTypes.oneOf(['12h', '24h']),
};

DateInput.defaultProps = {
  disabled: false,
  timeFormat: null,
};

export const dateSettingsFormDecorator = createDecorator({
  field: 'dateFormat',
  updates: dateFormat => {
    // clear the time format when it doesn't make sense for the selected date format
    if (!dateFormat.includes('%d')) {
      return {timeFormat: null};
    }
    return {};
  },
});

export const dateSettingsInitialData = {
  dateFormat: '%d/%m/%Y',
  timeFormat: null,
};

export function DateSettings() {
  const dateOptions = [
    '%d/%m/%Y',
    '%d.%m.%Y',
    '%m/%d/%Y',
    '%m.%d.%Y',
    '%Y/%m/%d',
    '%Y.%m.%d',
    '%m/%Y',
    '%m.%Y',
    '%Y',
  ].map(opt => ({
    key: opt,
    value: opt,
    text: opt.replace(
      /%([HMdmY])/g,
      (match, c) => ({H: 'hh', M: 'mm', d: 'DD', m: 'MM', Y: 'YYYY'}[c])
    ),
  }));
  const timeOptions = [
    {key: '12h', value: '12h', text: Translate.string('12 hours')},
    {key: '24h', value: '24h', text: Translate.string('24 hours')},
  ];
  return (
    <Form.Group widths="equal">
      <FinalDropdown
        name="dateFormat"
        label={Translate.string('Date format')}
        options={dateOptions}
        required
        selection
        fluid
      />
      <Field name="dateFormat" subscription={{value: true}}>
        {({input: {value: dateFormat}}) => (
          <FinalDropdown
            name="timeFormat"
            label={Translate.string('Time format')}
            options={timeOptions}
            placeholder={Translate.string('None')}
            disabled={!dateFormat.includes('%d')}
            parse={p.nullIfEmpty}
            selection
            fluid
          />
        )}
      </Field>
    </Form.Group>
  );
}

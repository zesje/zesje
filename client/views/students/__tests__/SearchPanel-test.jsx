import React from 'react';
import {mount} from 'enzyme';
import SearchPanel from '../SearchPanel';

test('Student id searchfield has focus on loading component', () => {
    const searchPanel = mount(<SearchPanel/>);
    const focusedElem = document.activeElement;

    expect(focusedElem.id).toEqual("panel-input");
});

/* eslint-env jest */
import React from 'react'
import { mount } from 'enzyme'
import SearchPanel from '../SearchPanel'

test('Student id searchfield has focus on loading component', () => {
  const panel = mount(<SearchPanel />)
  const focusedElem = document.activeElement

  expect(focusedElem).toEqual(panel.instance().searchInput.current)
})

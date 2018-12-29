/* eslint-env jest */
import React from 'react'
import {mount} from 'enzyme'
import SearchPanel from '../SearchPanel'

test('Student id searchfield has focus on loading component', () => {
  mount(<SearchPanel />)
  const focusedElem = document.activeElement

  expect(focusedElem.id).toEqual('panel-input')
})

import 'regenerator-runtime/runtime'

import React from 'react'
import { render } from 'react-dom'
import App from './App.jsx'

import TimeAgo from 'javascript-time-ago'

import en from 'javascript-time-ago/locale/en.json'

TimeAgo.addDefaultLocale(en)

const root = document.getElementById('root')
if (root == null) {
  throw new Error('no pad element')
} else {
  render(<App />, root)
}

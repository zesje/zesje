import React from 'react'
import { render } from 'react-dom'
import App from './App.jsx'

const root = document.getElementById('root')
if (root == null) {
  throw new Error('no pad element')
} else {
  render(<App />, root)
}

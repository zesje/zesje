import React from 'react'

import Hero from '../components/Hero.jsx'

import * as api from '../api.jsx'

class Email extends React.Component {
  render () {
    return (
      <React.Fragment>
        <Hero title='Email' subtitle='So the students get their feedback' />
      </React.Fragment>
    )
  }
}

export default Email

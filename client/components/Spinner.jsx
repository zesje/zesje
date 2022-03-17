import React from 'react'

/*
* See https://fontawesome.com/v5/search?m=free&c=spinners&s=solid for other spin icons.
*/
const Spinner = ({ color = 'info', icon = 'spinner' }) => (
  <p className='container has-text-centered'>
    <span className={'icon is-large has-text-' + color}>
      <i className={`fas fa-${icon} fa-2x fa-pulse`}></i>
    </span>
  </p>
)

export default Spinner

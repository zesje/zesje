import React from 'react'

import './Modal.css'
import Spinner from '../Spinner.jsx'

const ProgressModal = ({
  active = false,
  headerText = 'Loading...',
  onCancel = null
}) => {
  return (
    <div className={'modal ' + (active ? 'is-active' : '')}>
      <div className='modal-background' onClick={onCancel} />
      <div className='modal-card'>
        <header className='modal-card-head'>
          <p className='modal-card-title  '>{headerText}</p>
        </header>
        <section className='modal-card-body'>
          <Spinner />
        </section>
      </div>
      {onCancel && <button className='modal-close is-large' aria-label='close' onClick={onCancel} />}
    </div>
  )
}

export default ProgressModal

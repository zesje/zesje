import React from 'react'

import './Modal.css'

const ConfirmationModal = (props) => {
  let body = null
  if (props.contentText) {
    body =
      <section className='modal-card-body'>
        { props.contentText}
      </section>
  }

  return (
    <div className={'modal ' + (props.active ? 'is-active' : '')}>
      <div className='modal-background' onClick={props.onCancel} />
      <div className='modal-card'>
        <header className='modal-card-head'>
          <p className='modal-card-title  '>{props.headerText || 'Are you sure?'}</p>
        </header>
        {body}
        <footer className='modal-card-footer'>
          <div className='field is-grouped'>
            <button className={'button is-fullwidth is-footer is-left ' +
              (props.color || 'is-success')} onClick={props.onConfirm}>
              {props.confirmText || 'Save changes'}
            </button>
            <button className='button is-fullwidth is-footer is-right' onClick={props.onCancel}>
              {props.cancelText || 'Cancel'}
            </button>
          </div>
        </footer>
      </div>
      <button className='modal-close is-large' aria-label='close' />
    </div>
  )
}

export default ConfirmationModal

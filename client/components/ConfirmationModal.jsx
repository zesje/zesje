import React from 'react'

const ConfirmationModal = (props) => {
  return (
    <div className={'modal ' + (props.active ? 'is-active' : '')}>
      <div className='modal-background' onClick={props.onCancel} />
      <div className='modal-card'>
        <header className='modal-card-head'>
          <p className='modal-card-title  '>{props.contentText || 'Are you sure?'}</p>
        </header>
        <footer className='modal-card-footer'>
          <div className='field is-grouped'>
            <button className={'button is-fullwidth ' + (props.color || 'is-success')} onClick={props.onConfirm}>
              {props.confirmText || 'Save changes'}
            </button>
            <button className='button is-fullwidth' onClick={props.onCancel}>
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

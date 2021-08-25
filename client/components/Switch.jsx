import 'bulma-switch/dist/css/bulma-switch.min.css'
import React from 'react'

const Switch = (props) => {
  const id = `switch-${Math.random()}`
  return (
    <div className='field'>
      <input
        id={id}
        type='checkbox'
        className={'switch' + (props.color ? ` is-${props.color}` : '')}
        checked={props.value}
        value={props.value}
        {...props} />
      <label for={id} className='label' />
    </div>
  )
}
export default Switch

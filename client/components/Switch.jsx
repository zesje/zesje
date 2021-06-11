import React from 'react'

const Switch = (props) => {
  const id = `switch-${Math.random()}`
  return (
    <div className='field'>
      <label className={'switch' + (props.color ? ` is-${props.color}` : '')}>
        <input
          id={id}
          type='checkbox'
          checked={props.value}
          value='false'
          {...props}
        />
        <span className='check' />
      </label>
    </div>
  )
}
export default Switch

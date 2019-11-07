import React from 'react'

const ProgressBar = (props) => {
  const percentage = ((props.done / props.total) * 100).toFixed(1)

  return (
    <div className='level is-mobile'>
      <div className='level-item is-hidden-mobile'>
        <progress className='progress is-success' value={props.done} max={props.total}>
          {percentage}%
        </progress>
      </div>
      <div className='level-right'>
        <div className='level-item has-text-grey'>
          <i>{props.done} / {props.total}</i>
        </div>
        <div className='level-item has-text-success'>
          <b>{percentage}%</b>
        </div>
      </div>
    </div>
  )
}

export default ProgressBar

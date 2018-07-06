import React from 'react'

const ProgressBar = (props) => {
  const total = props.progress.length
  const done = props.progress.filter(obj => (obj[props.value] !== false && obj[props.value] !== null)).length
  const percentage = ((done / total) * 100).toFixed(1)

  return (
    <div className='level is-mobile'>
      <div className='level-item is-hidden-mobile'>
        <progress className='progress is-success' value={done}
          max={total}>
          {percentage}%</progress>
      </div>
      <div className='level-right'>
        <div className='level-item has-text-grey'>
          <i>{done} / {total}</i>
        </div>
        <div className='level-item has-text-success'>
          <b>{percentage}%</b>
        </div>
      </div>
    </div>
  )
}

export default ProgressBar

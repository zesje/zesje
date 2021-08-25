import React from 'react'

const Tooltip = (props) => {
  if (!props.text) {
    return null
  }

  const tooltipIcon = props.icon || 'comment'

  const tooltipLocation = props.location || 'right'

  let tooltipClass = 'icon tooltip is-tooltip-' + tooltipLocation
  if (props.text.length > 60) {
    tooltipClass += ' is-tooltip-multiline'
  }

  return (
    <span
      className={tooltipClass}
      data-tooltip={props.text}
      onClick={props.clickAction}
    >
      <i className={'fa fa-' + tooltipIcon} />
    </span>
  )
}

export default Tooltip

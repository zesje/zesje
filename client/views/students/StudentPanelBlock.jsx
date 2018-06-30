import React from 'react'

const StudentPanelBlock = (props) => {
  let panelClass = 'panel-block'
  const button = props.selected || props.matched

  if (button) {
    panelClass += ' button'
    panelClass += (props.matched) ? ' is-success' : ' is-link'
  } else panelClass += ' is-active'

  return (
    <div key={props.student.id}>
      <a className={panelClass}
        key={props.student.id} id={props.student.id} selected={props.selected} onClick={props.selectStudent}>
        <span className={'panel-icon' + (button ? ' has-text-white' : '')}>
          <i className='fa fa-user' />
        </span>
        {props.student.firstName + ' ' + props.student.lastName}
      </a>

      <div className={'panel-block' + (props.selected ? ' is-info' : ' is-hidden')}
        key='info' style={{ backgroundColor: '#dbdbdb' }}>

        <a className='panel-icon' onClick={() => props.editStudent(props.student)}>
          <i className='fa fa-pencil' />
        </a>
        {props.student.id}&emsp;
        <span className='panel-icon'>
          {props.matched ? <i className='fa fa-check' /> : null}
          {/* TODO: Show other submissions that student is assigned to */}
        </span>
        <i>{props.matched ? 'matched' : ''}</i>
      </div>

    </div>
  )
}

export default StudentPanelBlock

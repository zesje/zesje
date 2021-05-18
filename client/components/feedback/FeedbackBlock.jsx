import React from 'react'

import Tooltip from '../Tooltip.jsx'

class FeedbackBlock extends React.Component {
  state = {
    hover: {
      block: false,
      edit: false,
      filter: false
    }
  }

  filterIcons = {
    'no_filter': 'fa-filter',
    'required': 'fa-plus',
    'excluded': 'fa-minus'
  }
  filterColors = {
    'no_filter': '',
    'required': 'is-success',
    'excluded': 'is-danger'
  }

  leave = (component) => {
    this.setState(prevState => ({
      hover: {
        ...prevState.hover,
        [component]: false
      }
    }))
  }
  enter = (component) => {
    this.setState(prevState => ({
      hover: {
        ...prevState.hover,
        [component]: true
      }
    }))
  }

  toggle = () => {
    if (!this.state.hover['edit']) {
      this.props.toggleOption(this.props.feedback.id)
    }
  }

  render () {
    const shortcut = (this.props.index < 11 ? '' : 'shift + ') + this.props.index % 10
    return (
      <a
        className='panel-block feedback-item'
        onClick={this.props.grading ? this.toggle : this.props.editFeedback}
        style={this.props.selected ? {backgroundColor: '#209cee'} : {}}
        onMouseEnter={() => this.enter('block')} onMouseLeave={() => this.leave('block')}
      >
        <span
          style={{ width: '1.5rem' }}
          className={'tag' +
            (this.props.checked ? ' is-link' : '') +
            ((this.props.showIndex && this.props.index <= 20) ? ' tooltip is-tooltip-active is-tooltip-left' : '')}
          data-tooltip={shortcut}>
          {this.props.feedback.score}
        </span>
        <span className={'grow'} style={{ paddingLeft: '0.5em' }}>
          {this.props.feedback.name}
          <Tooltip text={this.props.feedback.description} />
        </span>
        <button
          className={'button is-pulled-right is-small is-light' +
          (this.state.hover['block'] ? '' : ' is-invisible') +
          (this.state.hover['edit'] ? ' is-link' : '')}
          onMouseEnter={() => this.enter('edit')} onMouseLeave={() => this.leave('edit')}
          onClick={this.props.editFeedback}
        >
          <i className='fa fa-pencil' />
        </button>
        <div
          className={`popover is-popover-right button is-pulled-right is-small is-light
          ${(this.props.filterMode !== 'no_filter' ? 'is-inverted' : (this.state.hover['block'] ? '' : 'is-invisible'))}
          ${this.state.hover['filter'] ? 'is-link' : ''}
          ${this.filterColors[this.props.filterMode]}`}
          onMouseEnter={() => this.enter('filter')} onMouseLeave={() => this.leave('filter')}
        >
          <i className={`fa ${this.filterIcons[this.props.filterMode]}`} />
          <div style={{display: this.state.hover['filter'] ? '' : 'none', position: 'absolute', left: 0, top: 0, width: '4em', height: '2em'}} onClick={e => this.props.applyFilter(e, 'no_filter')} />
          <div className='popover-content' style={{display: 'grid', gridAutoFlow: 'column', gap: '1em'}}>
            <button className={`button popover-trigger is-inverted fa ${this.filterIcons.required} ${this.filterColors['required']}`} onClick={e => this.props.applyFilter(e, 'required')} />
            <button className={`button popover-trigger is-inverted fa ${this.filterIcons.excluded} ${this.filterColors['excluded']}`} onClick={(e) => this.props.applyFilter(e, 'excluded')} />
          </div>
        </div>
      </a>
    )
  }
}

export default FeedbackBlock

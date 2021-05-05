import React from 'react'

import Tooltip from '../Tooltip.jsx'

class FeedbackBlock extends React.Component {
  state = {
    hover: {
      block: false,
      edit: false,
      filter: false
    },
    filterMode: 'dont_care' // 'dont_care' 'required' 'not_required'
  }

  filterIcons = {
    'dont_care': 'fa-filter',
    'required': 'fa-plus-square',
    'not_required': 'fa-minus-square'
  }
  filterColors = {
    'dont_care': '',
    'required': 'hsl(141, 53%, 53%)',
    'not_required': 'hsl(348, 100%, 61%)'
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

  applyFilter = (e, newFilterMode) => {
    e.stopPropagation()
    this.setState({
      filterMode: this.state.filterMode === newFilterMode ? 'dont_care' : newFilterMode
    })
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
        <span
          className={'tag is-pulled-right' +
          (this.state.hover['block'] ? '' : ' is-invisible') +
          (this.state.hover['edit'] ? ' is-link' : '')}
          onMouseEnter={() => this.enter('edit')} onMouseLeave={() => this.leave('edit')}
          onClick={this.props.editFeedback}
        >
          <i className='fa fa-pencil' />
        </span>
        <span
          className={'popover is-popover-bottom tag is-pulled-right ' +
          (this.state.hover['block'] || this.state.filterMode === 'required' || this.state.filterMode === 'not_required' ? '' : ' is-invisible') +
          (this.state.hover['filter'] ? ' is-link' : '')}
          onMouseEnter={() => this.enter('filter')} onMouseLeave={() => this.leave('filter')}
        >
          <i className={'fa ' + this.filterIcons[this.state.filterMode]} style={{color: this.filterColors[this.state.filterMode]}} />
          <div style={{display: this.state.hover['filter'] ? '' : 'none', position: 'absolute', width: '4em', height: '4em'}} onClick={e => this.applyFilter(e, 'dont_care')} />
          <div className='popover-content' style={{}}>
            <button className={'button popover-trigger fa ' + this.filterIcons.required} style={{color: this.filterColors['required']}} onClick={e => this.applyFilter(e, 'required')} />
            <button className={'button popover-trigger fa ' + this.filterIcons.not_required} style={{color: this.filterColors['not_required']}} onClick={(e) => this.applyFilter(e, 'not_required')} />
          </div>
        </span>
      </a>
    )
  }
}

export default FeedbackBlock

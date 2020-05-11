import React from 'react'

import Tooltip from '../Tooltip.jsx'

class FeedbackBlock extends React.Component {
  state = {
    hover: {
      block: false,
      edit: false
    }
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
        <span style={{ paddingLeft: '0.5em' }}>
          {this.props.feedback.name}
        </span>
        <Tooltip text={this.props.feedback.description} />
        <span
          className={'tag' +
          (this.state.hover['block'] ? '' : ' is-hidden') +
          (this.state.hover['edit'] ? ' is-link' : '')}
          onMouseEnter={() => this.enter('edit')} onMouseLeave={() => this.leave('edit')}
          onClick={this.props.editFeedback}
        >
          <i className='fa fa-pencil' />
        </span>

      </a>
    )
  }
}

export default FeedbackBlock

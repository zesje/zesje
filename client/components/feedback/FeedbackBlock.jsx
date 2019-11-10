import React from 'react'

import Tooltip from '../Tooltip.jsx'

class FeedbackBlock extends React.Component {
  state = {
    hover: false
  }
  leave = () => {
    this.setState({
      hover: false
    })
  }
  enter = () => {
    this.setState({
      hover: true
    })
  }

  toggle = () => {
    if (!this.state.hover) {
      this.props.toggleOption(this.props.feedback.id)
    }
  }

  render () {
    const shortcut = (this.props.index < 11 ? '' : 'shift + ') + this.props.index % 10
    return (
      <a
        className={this.props.grading ? 'panel-block is-active' : 'panel-block'}
        onClick={this.props.grading ? this.toggle : this.props.editFeedback}
        style={this.props.selected ? {backgroundColor: '#209cee'} : {}}
      >
        <span
          className={'panel-icon' + ((this.props.showIndex && this.props.index <= 20)
            ? ' tooltip is-tooltip-active is-tooltip-left' : '')}
          data-tooltip={shortcut}
        >
          {this.props.grading &&
            <i className={'fa fa-' + (this.props.checked ? 'check-square-o' : 'square-o')} />
          }
        </span>
        <span style={{ width: '80%' }}>
          {this.props.feedback.name}
        </span>
        <Tooltip text={this.props.feedback.description} />
        <div className='field is-grouped'>
          <div className='control'>
            <div className='tags has-addons'>
              <span className='tag is-link'>{this.props.feedback.score}</span>
              <span className={'tag' + (this.state.hover ? ' is-white' : '')}
                onMouseEnter={this.enter} onMouseLeave={this.leave} onClick={this.props.editFeedback}>
                <i className='fa fa-pencil' />
              </span>
            </div>
          </div>
        </div>
      </a>
    )
  }
}

export default FeedbackBlock

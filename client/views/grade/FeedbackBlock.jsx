import React from 'react'

import * as api from '../../api.jsx'

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
      api.put('solution/' + this.props.uri, {
        id: this.props.feedback.id,
        graderID: this.props.graderID
      })
        .then(result => {
          this.props.updateSubmission()
        })
    }
  }

  render () {
    return (
      <a className='panel-block is-active' onClick={this.toggle}
        style={this.props.selected ? {backgroundColor: '#209cee'} : {}}
      >
        <span
          className={'panel-icon' + ((this.props.showIndex && this.props.index <= 10)
            ? ' tooltip is-tooltip-active is-tooltip-left' : '')}
          data-tooltip={this.props.index % 10}
        >
          <i className={'fa fa-' + (this.props.checked ? 'check-square-o' : 'square-o')} />
        </span>
        <span style={{ width: '80%' }}>
          {this.props.feedback.name}
        </span>
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

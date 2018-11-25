import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx'

class FeedbackPanel extends React.Component {
  state = {
    remark: '',
    problemID: null,
    submissionID: null
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.problemID !== nextProps.problem.id || prevState.submissionID !== nextProps.submissionID) {
      return {
        remark: nextProps.solution.remark,
        problemID: nextProps.problem.id,
        submissionID: nextProps.submissionID
      }
    } else return null
  }

  saveRemark = () => {
    api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
      remark: this.state.remark,
      graderID: this.props.graderID
    })
      .then(success => {
        if (!success) Notification.error('Remark not saved!')
      })
  }

  changeRemark = (event) => {
    this.setState({
      remark: event.target.value
    })
  }

  render () {
    const blockURI = this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id

    let totalScore = 0
    for (let i = 0; i < this.props.solution.feedback.length; i++) {
      const probIndex = this.props.problem.feedback.findIndex(fb => fb.id === this.props.solution.feedback[i])
      if (probIndex >= 0) totalScore += this.props.problem.feedback[probIndex].score
    }

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Total:&nbsp;<b>{totalScore}</b>
        </p>
        {this.props.problem.feedback.map(feedback =>
          <FeedbackBlock key={feedback.id} uri={blockURI} graderID={this.props.graderID}
            feedback={feedback} checked={this.props.solution.feedback.includes(feedback.id)}
            editFeedback={() => this.props.editFeedback(feedback)} updateSubmission={this.props.updateSubmission} />
        )}
        <div className='panel-block'>
          <textarea className='textarea' rows='2' placeholder='remark' value={this.state.remark} onBlur={this.saveRemark} onChange={this.changeRemark} />
        </div>
        <div className='panel-block'>
          <button className='button is-link is-outlined is-fullwidth' onClick={() => this.props.editFeedback()}>
            <span className='icon is-small'>
              <i className='fa fa-plus' />
            </span>
            <span>option</span>
          </button>
        </div>
      </nav>
    )
  }
}
export default FeedbackPanel

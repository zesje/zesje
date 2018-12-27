import React from 'react'
import Mousetrap from 'mousetrap'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

import FeedbackBlock from './FeedbackBlock.jsx'

class FeedbackPanel extends React.Component {
  feedbackBlock = React.createRef();

  state = {
    remark: '',
    problemID: null,
    submissionID: null,
    selectedFeedbackIndex: null
  }

  componentWillUnmount = () => {
    Mousetrap.unbind(['up', 'i'])
    Mousetrap.unbind(['down', 'k'])
    Mousetrap.unbind(['space'])
  }

  componentDidMount = () => {
    Mousetrap.bind(['up', 'i'], (event) => {
      event.preventDefault()
      this.prevOption()
    })
    Mousetrap.bind(['down', 'k'], (event) => {
      event.preventDefault()
      this.nextOption()
    })
    Mousetrap.bind(['space'], (event) => {
      event.preventDefault()
      this.toggleSelectedOption()
    })
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.problemID !== nextProps.problem.id || prevState.submissionID !== nextProps.submissionID) {
      return {
        remark: nextProps.solution.remark,
        problemID: nextProps.problem.id,
        submissionID: nextProps.submissionID,
        selectedFeedbackIndex: null
      }
    } else return null
  }

  prevOption = () => {
    if (this.props.problem.feedback.length === 0) return
    let newIndex = this.props.problem.feedback.length - 1
    if (this.state.selectedFeedbackIndex !== null && this.state.selectedFeedbackIndex !== 0) {
      newIndex = this.state.selectedFeedbackIndex - 1
    }
    this.setState({
      selectedFeedbackIndex: newIndex
    })
  }

  nextOption = () => {
    if (this.props.problem.feedback.length === 0) return
    let newIndex = 0
    if (this.state.selectedFeedbackIndex !== null &&
      this.state.selectedFeedbackIndex + 1 < this.props.problem.feedback.length) {
      newIndex = this.state.selectedFeedbackIndex + 1
    }
    this.setState({
      selectedFeedbackIndex: newIndex
    })
  }

  toggleSelectedOption = () => {
    if (this.feedbackBlock.current) {
      this.feedbackBlock.current.toggle()
    }
  }

  saveRemark = () => {
    api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
      remark: this.state.remark,
      graderID: this.props.graderID
    })
      .then(success => {
        this.props.updateSubmission()
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

    let selectedFeedbackId = this.state.selectedFeedbackIndex !== null &&
      this.props.problem.feedback[this.state.selectedFeedbackIndex].id

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Total:&nbsp;<b>{totalScore}</b>
        </p>
        {this.props.problem.feedback.map(feedback =>
          <FeedbackBlock key={feedback.id} uri={blockURI} graderID={this.props.graderID}
            feedback={feedback} checked={this.props.solution.feedback.includes(feedback.id)}
            editFeedback={() => this.props.editFeedback(feedback)} updateSubmission={this.props.updateSubmission}
            ref={(selectedFeedbackId === feedback.id) ? this.feedbackBlock : null}
            selected={selectedFeedbackId === feedback.id} />
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

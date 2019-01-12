import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

import withShortcuts from '../../components/ShortcutBinder.jsx'
import FeedbackBlock from './FeedbackBlock.jsx'

class FeedbackPanel extends React.Component {
  feedbackBlock = React.createRef();

  state = {
    remark: '',
    problemID: null,
    submissionID: null,
    selectedFeedbackIndex: null
  }

  componentDidMount = () => {
    this.props.bindShortcut(['up', 'k'], (event) => {
      event.preventDefault()
      this.prevOption()
    })
    this.props.bindShortcut(['down', 'j'], (event) => {
      event.preventDefault()
      this.nextOption()
    })
    this.props.bindShortcut(['space'], (event) => {
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

  setOptionIndex = (newIndex) => {
    if (this.props.problem.feedback.length === 0) return
    let length = this.props.problem.feedback.length
    newIndex = ((newIndex % length) + length) % length
    this.setState({
      selectedFeedbackIndex: newIndex
    })
  }

  prevOption = () => {
    let index = this.state.selectedFeedbackIndex !== null ? this.state.selectedFeedbackIndex : 0
    this.setOptionIndex(index - 1)
  }

  nextOption = () => {
    let index = this.state.selectedFeedbackIndex !== null ? this.state.selectedFeedbackIndex : -1
    this.setOptionIndex(index + 1)
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
        {this.props.problem.feedback.map((feedback, index) =>
          <FeedbackBlock key={feedback.id} uri={blockURI} graderID={this.props.graderID}
            feedback={feedback} checked={this.props.solution.feedback.includes(feedback.id)}
            editFeedback={() => this.props.editFeedback(feedback)} updateSubmission={this.props.updateSubmission}
            ref={(selectedFeedbackId === feedback.id) ? this.feedbackBlock : null}
            selected={selectedFeedbackId === feedback.id} showIndex={this.props.showTooltips} index={index + 1} />
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
export default withShortcuts(FeedbackPanel)

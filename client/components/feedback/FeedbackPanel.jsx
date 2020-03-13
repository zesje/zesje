import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

import withShortcuts from '../ShortcutBinder.jsx'
import FeedbackBlock from './FeedbackBlock.jsx'

class FeedbackPanel extends React.Component {
  feedbackBlock = React.createRef();

  state = {
    selectedFeedbackIndex: null,
    remark: '',
    // Have to keep submissionID and problemID in state,
    // to be able to decide when to derive remark from properties.
    submissionID: null,
    problemID: null
  }

  componentDidMount = () => {
    if (this.props.grading) {
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
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.problemID !== nextProps.problem.id || prevState.submissionID !== nextProps.submissionID) {
      return {
        remark: nextProps.grading && nextProps.solution.remark,
        selectedFeedbackIndex: null,
        submissionID: nextProps.submissionID,
        problemID: nextProps.problem.id
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
    if (!this.props.solution.graded_at && this.state.remark.replace(/\s/g, '').length === 0) return
    api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
      remark: this.state.remark,
      graderID: this.props.graderID
    }).then(success => {
      this.props.setSubmission(this.props.submissionID)
      if (!success) Notification.error('Remark not saved!')
    })
  }

  changeRemark = (event) => {
    this.setState({
      remark: event.target.value
    })
  }

  /**
   * Blurs the remark box when pressing escape or enter (shift+enter preserves newlines)
   * @param event the event
   */
  keyMap = (event) => {
    if (event.keyCode === 27 || (event.keyCode === 13 && !event.shiftKey)) {
      event.preventDefault()
      event.target.blur()
    }
  }

  render () {
    const blockURI = this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id

    let totalScore = 0
    if (this.props.grading) {
      for (let i = 0; i < this.props.solution.feedback.length; i++) {
        const probIndex = this.props.problem.feedback.findIndex(fb => fb.id === this.props.solution.feedback[i])
        if (probIndex >= 0) totalScore += this.props.problem.feedback[probIndex].score
      }
    }

    let selectedFeedbackId = this.state.selectedFeedbackIndex !== null &&
      this.props.problem.feedback[this.state.selectedFeedbackIndex].id
    return (
      <React.Fragment>
        {this.props.grading &&
          <div className='panel-heading level' style={{marginBottom: 0 + 'px'}}>
            <p className='level-left'>Total:&nbsp;<b>{totalScore}</b></p>
            <div className='level-right'>
              <div className={this.props.showTooltips ? ' tooltip is-tooltip-active is-tooltip-top' : ''}
                data-tooltip='approve/set aside feedback: a'>
                <button title={this.props.solution.feedback.length === 0 && 'At least one feedback option must be selected'}
                  className='button is-info'
                  disabled={this.props.solution.feedback.length === 0}
                  onClick={this.props.toggleApprove}>
                  {this.props.solution.graded_by === null ? 'Approve' : 'Set aside'}
                </button>
              </div>
            </div>
          </div>
        }
        {this.props.problem.feedback.map((feedback, index) =>
          <FeedbackBlock key={feedback.id} uri={blockURI} graderID={this.props.graderID}
            feedback={feedback} checked={this.props.grading && this.props.solution.feedback.includes(feedback.id)}
            editFeedback={() => this.props.editFeedback(feedback)} toggleOption={this.props.toggleOption}
            ref={(selectedFeedbackId === feedback.id) ? this.feedbackBlock : null} grading={this.props.grading}
            submissionID={this.props.submissionID} selected={selectedFeedbackId === feedback.id || feedback.highlight}
            showIndex={this.props.showTooltips} index={index + 1} />
        )}
        {this.props.grading &&
          <div className='panel-block'>
            <textarea className='textarea' rows='2' placeholder='Remark' value={this.state.remark} onBlur={this.saveRemark} onChange={this.changeRemark} onKeyDown={this.keyMap} />
          </div>
        }
        <div className='panel-block'>
          <button className='button is-link is-outlined is-fullwidth' onClick={() => this.props.editFeedback()}>
            <span className='icon is-small'>
              <i className='fa fa-plus' />
            </span>
            <span>option</span>
          </button>
        </div>
      </React.Fragment>
    )
  }
}
export default withShortcuts(FeedbackPanel)

import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

import withShortcuts from '../ShortcutBinder.jsx'
import FeedbackBlock from './FeedbackBlock.jsx'
import FeedbackBlockEdit from './FeedbackBlockEdit.jsx'

import './Feedback.css'

class FeedbackPanel extends React.Component {
  feedbackBlock = React.createRef();

  state = {
    selectedFeedbackIndex: null,
    feedbackToEditId: 0,
    remark: '',
    // Have to keep submissionID and problemID in state,
    // to be able to decide when to derive remark from properties.
    submissionID: null,
    problemID: null
  }

  /**
   * Enter the feedback editing view for a feedback option.
   * @param feedback the feedback to edit.
   */
  editFeedback = (feedbackId) => {
    this.setState({
      feedbackToEditId: feedbackId
    })
  }
  /**
   * Go back to all the feedback options.
   * Updates the problem to make sure changes to feedback options are reflected.
   */
  backToFeedback = () => {
    this.setState({
      feedbackToEditId: 0
    })
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
        feedbackToEditId: 0,
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
          <div className='panel-heading level' style={{marginBottom: '0px'}}>
            <div className='level-left'>
              {this.props.solution.feedback.length !== 0 && <p>Total:&nbsp;<b>{totalScore}</b></p>}
            </div>
            <div className='level-right'>
              <div className={this.props.showTooltips ? ' tooltip is-tooltip-active is-tooltip-top' : ''}
                data-tooltip='approve/set aside feedback: a'>
                <button title={this.props.solution.feedback.length === 0 ? 'At least one feedback option must be selected' : ''}
                  className='button is-info'
                  disabled={this.props.solution.feedback.length === 0}
                  onClick={this.props.toggleApprove}>
                  {this.props.solution.graded_by === null ? 'Approve' : 'Set aside'}
                </button>
              </div>
            </div>
          </div>
        }
        {this.props.problem.feedback.map((feedback, index) => (
          feedback.id !== this.state.feedbackToEditId
            ? <FeedbackBlock key={feedback.id} uri={blockURI} graderID={this.props.graderID}
              feedback={feedback} checked={this.props.grading && this.props.solution.feedback.includes(feedback.id)}
              editFeedback={() => this.editFeedback(feedback.id)} toggleOption={this.props.toggleOption}
              ref={(selectedFeedbackId === feedback.id) ? this.feedbackBlock : null} grading={this.props.grading}
              submissionID={this.props.submissionID} selected={selectedFeedbackId === feedback.id || feedback.highlight}
              showIndex={this.props.showTooltips}
              index={index + 1}
              showIcons={this.state.feedbackToEditId !== -1}
              filterMode={this.props.feedbackFilters[feedback.id] || 'no_filter'}
              applyFilter={(e, newFilterMode) => this.props.applyFilter(e, feedback.id, newFilterMode)}
            />
            : <FeedbackBlockEdit key={feedback.id} feedback={feedback} problemID={this.state.problemID}
              goBack={this.backToFeedback} showCancel={this.state.feedbackToEditId !== -1} updateFeedback={this.props.updateFeedback} />
        ))}
        {(this.state.feedbackToEditId === -1)
          ? <FeedbackBlockEdit feedback={null} problemID={this.state.problemID} goBack={this.backToFeedback}
            updateFeedback={this.props.updateFeedback} />
          : <div className='panel-block'>
            <button className='button is-link is-outlined is-fullwidth' onClick={() => this.editFeedback(-1)}>
              <span className='icon is-small'>
                <i className='fa fa-plus' />
              </span>
              <span>options</span>
            </button>
          </div>
        }
        {(this.state.feedbackToEditId === -1) &&
        <div className='panel-block'>
          <button className='button is-link is-outlined is-fullwidth' onClick={() => this.backToFeedback()}>
            <span className='icon is-small'>
              <i className='fa fa-chevron-left' />
            </span>
            <span>back</span>
          </button>
        </div>
        }
        {this.props.grading &&
          <div className='panel-block'>
            <textarea className='textarea' rows='2' placeholder='Remark' value={this.state.remark} onBlur={this.saveRemark} onChange={this.changeRemark} onKeyDown={this.keyMap} />
          </div>
        }
      </React.Fragment>
    )
  }
}
export default withShortcuts(FeedbackPanel)

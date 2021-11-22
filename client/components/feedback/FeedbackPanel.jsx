import React from 'react'

import { toast } from 'bulma-toast'

import * as api from '../../api.jsx'

import withShortcuts from '../ShortcutBinder.jsx'

import FeedbackMenu from './FeedbackMenu.jsx'

import './Feedback.css'

class FeedbackPanel extends React.Component {
  state = {
    remark: '',
    // Have to keep submissionID and problemID in state,
    // to be able to decide when to derive remark from properties.
    submissionID: null,
    problemID: null
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.problemID !== nextProps.problem.id || prevState.submissionID !== nextProps.submissionID) {
      return {
        remark: nextProps.solution.remark,
        submissionID: nextProps.submissionID,
        problemID: nextProps.problem.id
      }
    }

    return null
  }

  saveRemark = () => {
    if (!this.props.solution.graded_at && this.state.remark.replace(/\s/g, '').length === 0) return
    api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
      remark: this.state.remark
    }).then(success => {
      this.props.setSubmission(this.props.submissionID)
      if (!success) toast({ message: 'Remark not saved!', type: 'is-danger' })
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
    const solution = this.props.solution
    let totalScore = 0
    for (let i = 0; i < solution.feedback.length; i++) {
      totalScore += this.props.problem.feedback[solution.feedback[i]].score
    }

    return (
      <>
        <div className='panel-heading level' style={{ marginBottom: 0 }}>
          <div className='level-left'>
            {solution.feedback.length !== 0 && <p>Total:&nbsp;<b>{totalScore}</b></p>}
          </div>
          <div className='level-right'>
            <div
              className={'has-tooltip-arrow' + (this.props.showTooltips ? ' has-tooltip-active' : '')}
              data-tooltip='approve/set aside feedback: a'
            >
              <button
                title={
                  solution.feedback.length === 0
                    ? 'At least one feedback option must be selected'
                    : (solution.valid ? '' : 'Several exclusive options are checked at the same time.')
                }
                className='button is-info'
                disabled={solution.feedback.length === 0 || !solution.valid}
                onClick={this.props.toggleApprove}
              >
                {solution.graded_by === null ? 'Approve' : 'Set aside'}
              </button>
            </div>
          </div>
        </div>
        <FeedbackMenu {...this.props} grading />
        <div className='panel-block'>
          <textarea
            className='textarea'
            rows='2'
            placeholder='Remark'
            value={this.state.remark}
            onBlur={this.saveRemark}
            onChange={this.changeRemark}
            onKeyDown={this.keyMap} />
        </div>
      </>
    )
  }
}
export default withShortcuts(FeedbackPanel)

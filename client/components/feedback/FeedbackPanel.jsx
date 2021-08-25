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
        remark: nextProps.grading && nextProps.solution.remark,
        submissionID: nextProps.submissionID,
        problemID: nextProps.problem.id
      }
    }

    return null
  }

  saveRemark = () => {
    if (!this.props.solution.graded_at && this.state.remark.replace(/\s/g, '').length === 0) return
    api.post('solution/' + this.props.examID + '/' + this.props.submissionID + '/' + this.props.problem.id, {
      remark: this.state.remark,
      graderID: this.props.graderID
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
    let totalScore = 0
    if (this.props.grading) {
      for (let i = 0; i < this.props.solution.feedback.length; i++) {
        totalScore += this.props.problem.feedback[this.props.solution.feedback[i]].score
      }
    }

    return (
      <React.Fragment>
        {this.props.grading &&
          <div className='panel-heading level' style={{marginBottom: 0}}>
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
        <FeedbackMenu {...this.props} />
        {this.props.grading &&
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
        }
      </React.Fragment>
    )
  }
}
export default withShortcuts(FeedbackPanel)

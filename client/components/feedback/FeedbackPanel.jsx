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
    problemID: null,
    parentID: null
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
      feedbackToEditId: 0,
      parent: null
    })
  }

  addParent = (feedbackId, parent) => {
    this.editFeedback(feedbackId)
    this.setState({
      parent: parent
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
  * Adds indexes based on pre-order sorting.
  * @param root the root FO of the problem
  * @returns {*} the root FO now with index
  */
  addIndex = (root) => {
    let index = 0
    const stack = [root]
    while (stack.length > 0) {
      const current = stack.shift()
      current.index = index++
      stack.unshift(...current.children)
    }
    return root
  }

  /**
  * Finds the FO that matches the given index (used for shortcuts)
  * @param feedback the feedback to check if it matches.
  * @param index the index to match
  * @returns {null|*} return null if no match, or else the matching FO
  */
  findIndex = (feedback, index) => {
    if (feedback.index === index) {
      return feedback
    }
    for (let i = 0; i < feedback.children.length; i++) {
      let fb = this.findIndex(feedback.children[i], index)
      if (fb !== null) {
        return fb
      }
    }
    return null
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

    getFeedbackElement = (feedback, index, feedbackPanel) => {
      let indexed = this.addIndex(this.props.problem.root)
      const selectedFeedbackId = feedbackPanel.state.selectedFeedbackIndex !== null &&
      this.findIndex(indexed, this.state.selectedFeedbackIndex).id
      const blockURI = feedbackPanel.props.examID + '/' + feedbackPanel.props.submissionID + '/' + feedbackPanel.props.problem.id
      return feedback.id !== feedbackPanel.state.feedbackToEditId
        ? <FeedbackBlock key={feedback.id} uri={blockURI} graderID={feedbackPanel.props.graderID}
          feedback={feedback}
          checked={feedbackPanel.props.grading && feedbackPanel.props.solution.feedback.includes(feedback.id)}
          editFeedback={() => this.editFeedback(feedback.id)} toggleOption={feedbackPanel.props.toggleOption}
          ref={(selectedFeedbackId === feedback.id) ? feedbackPanel.feedbackBlock : null}
          grading={feedbackPanel.props.grading}
          submissionID={feedbackPanel.props.submissionID}
          selected={selectedFeedbackId === feedback.id || feedback.highlight}
          showIndex={feedbackPanel.props.showTooltips}
          index={index}
          filterMode={this.props.grading ? this.props.feedbackFilters[feedback.id] || 'no_filter' : 'no_filter'}
          applyFilter={(e, newFilterMode) => feedbackPanel.props.applyFilter(e, feedback.id, newFilterMode)}
          children={feedback.children}
          feedbackPanel={feedbackPanel}
        />
        : <FeedbackBlockEdit key={feedback.id} feedback={feedback} problemID={feedbackPanel.state.problemID}
          goBack={feedbackPanel.backToFeedback} updateFeedback={feedbackPanel.props.updateFeedback} children={feedback.children} feedbackPanel={feedbackPanel} />
    }

    render () {
      let totalScore = 0
      if (this.props.grading) {
        for (let i = 0; i < this.props.solution.feedback.length; i++) {
          const probIndex = this.props.problem.feedback.findIndex(fb => fb.id === this.props.solution.feedback[i])
          if (probIndex >= 0) totalScore += this.props.problem.feedback[probIndex].score
        }
      }
      let root = this.addIndex(this.props.problem.root)
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
          <div className='panel-block' style={{display: 'block'}}>
            <div className='menu'>
              {root.children.map((fbs) =>
                <ul key={fbs.index} className='menu-list'>
                  {this.getFeedbackElement(fbs, fbs.index, this)}
                </ul>
              )}
            </div>
          </div>
          {(this.state.feedbackToEditId === -1)
            ? <FeedbackBlockEdit feedback={null} problemID={this.state.problemID} goBack={this.backToFeedback}
              updateFeedback={this.props.updateFeedback} parent={this.state.parent} children={null} feedbackPanel={null} />
            : <div className='panel-block'>
              <button className='button is-link is-outlined is-fullwidth' onClick={() => this.addParent(-1, this.props.problem.root)}>
                <span className='icon is-small'>
                  <i className='fa fa-plus' />
                </span>
                <span>option</span>
              </button>
              <div className='dropdown is-hoverable is-right is-up'>
                <div className='dropdown-trigger' />
                <button className='button is-link is-outlined' aria-controls="dropdown-menu-FO-parent">
                  <span className='icon is-small'>
                    <i className='fa fa-chevron-down' />
                  </span>
                </button>
                <div className='dropdown-menu' id='dropdown-menu-FO-parent' role='menu'>
                  <div className='dropdown-content'>
                    <div className='dropdown-item'>
                      <p><b>Parent feedback:</b></p>
                    </div>
                    {this.props.problem.feedback.filter(feedback => feedback.parent != null).map((feedback, index) =>
                      <a key={index} className='dropdown-item' onClick={() => this.addParent(-1, feedback)}>
                        {feedback.name}
                      </a>
                    )}
                  </div>
                </div>
              </div>
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

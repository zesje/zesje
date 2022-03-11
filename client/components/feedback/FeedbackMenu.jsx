import React from 'react'

import withShortcuts from '../ShortcutBinder.jsx'
import FeedbackBlockEdit from './FeedbackBlockEdit.jsx'
import { indexFeedbackOptions, findFeedbackByIndex, FeedbackList } from './FeedbackUtils.jsx'

import './Feedback.css'

class FeedbackMenu extends React.Component {
  feedbackBlock = React.createRef();

  state = {
    selectedFeedback: null,
    feedbackToEditId: -1,
    parentId: -1,
    indexedFeedback: null,
    problemID: -1
  }

  componentDidMount = () => {
    if (this.props.grading) {
      this.props.bindShortcut(['up', 'k'], (event) => {
        event.preventDefault()
        this.navigateOptions(-1)
      })
      this.props.bindShortcut(['down', 'j'], (event) => {
        event.preventDefault()
        this.navigateOptions(1)
      })
      this.props.bindShortcut(['space'], (event) => {
        event.preventDefault()
        this.toggleSelectedOption()
      })
    }
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    const indexedFeedback = indexFeedbackOptions(nextProps.problem.feedback, nextProps.problem.root_feedback_id)

    if (prevState.problemID !== nextProps.problem.id) {
      return {
        indexedFeedback,
        selectedFeedback: null,
        feedbackToEditId: 0,
        parentId: -1,
        problemID: nextProps.problem.id
      }
    }

    return {
      indexedFeedback
    }
  }

  /**
   * Enter the feedback editing view for a feedback option.
   * Pass a null or negative id to stop editing.
   * @param feedbackId the id of the feedback to edit.
   * @param parent the parent feedback option, if any
   */
  editFeedback = (feedbackId, parentId) => {
    this.setState({
      feedbackToEditId: feedbackId,
      parentId
    })
  }

  setOptionIndex = (newIndex) => {
    const length = Object.keys(this.props.problem.feedback).length
    if (length === 0) return

    newIndex = ((newIndex % length) + length) % length
    this.setState({
      selectedFeedback: findFeedbackByIndex(this.state.indexedFeedback, newIndex)
    })
  }

  navigateOptions = (direction) => {
    const index = this.state.selectedFeedback !== null ? this.state.selectedFeedback.index : 0
    this.setOptionIndex(index + direction)
  }

  toggleSelectedOption = () => {
    if (this.feedbackBlock.current) {
      this.feedbackBlock.current.toggle()
    }
  }

  render () {
    const rootFO = this.state.indexedFeedback[this.props.problem.root_feedback_id]

    return (
      <React.Fragment>
        <div className='panel-block' style={{ display: 'block' }}>
          <div className='menu'>
            {<FeedbackList
              feedback={rootFO}
              indexedFeedback={this.state.indexedFeedback}
              selectedFeedbackId={this.state.selectedFeedback && this.state.selectedFeedback.id}
              editFeedback={this.editFeedback}
              problemID={this.props.problem.id}
              updateFeedback={this.props.updateFeedback}
              feedbackToEditId={this.state.feedbackToEditId}
              grading={this.props.grading}
              // only necessary when grading
              checkedFeedback={this.props.grading && this.props.solution.feedback}
              toggleOption={this.props.toggleOption}
              showTooltips={this.props.showTooltips}
              feedbackFilters={this.props.feedbackFilters}
              applyFilter={this.props.applyFilter}
              blockRef={this.feedbackBlock}
              />
            }
          </div>
        </div>
        {this.state.feedbackToEditId === -1
          ? <FeedbackBlockEdit
            feedback={null}
            parentId={this.state.parentId}
            problemID={this.props.problem.id}
            goBack={() => this.editFeedback(0, -1)}
            updateFeedback={this.props.updateFeedback} />
          : <div className='panel-block'>
            <button
              className='button is-link is-outlined is-fullwidth'
              onClick={() => this.editFeedback(-1, this.props.problem.root_feedback_id)}>
              <span className='icon is-small'>
                <i className='fa fa-plus' />
              </span>
              <span>option</span>
            </button>
            {this.props.problem.mc_options.length === 0 && Object.keys(this.state.indexedFeedback).length > 1 &&
              <div className='dropdown is-hoverable is-right is-up'>
                <div className='dropdown-trigger' />
                <button className='button is-link is-outlined' aria-controls='dropdown-menu-FO-parent'>
                  <span className='icon is-small'>
                    <i className='fa fa-chevron-down' />
                  </span>
                </button>
                <div className='dropdown-menu is-fullwidth' id='dropdown-menu-FO-parent' role='menu'>
                  <div className='dropdown-content'>
                    <div className='dropdown-item'>
                      <p><b>Parent feedback:</b></p>
                    </div>
                    {Object.keys(this.state.indexedFeedback)
                      // id and root_feedback_id have different types so type check comparison (!==) does not work
                      .filter(id => id != this.props.problem.root_feedback_id) // eslint-disable-line eqeqeq
                      .map((id, index) =>
                        <a key={'dropdown-parent-' + index}
                          className='dropdown-item has-text-overflow'
                          onClick={() => this.editFeedback(-1, id)}>
                          {this.state.indexedFeedback[id].name}
                        </a>
                      )}
                  </div>
                </div>
              </div>}
          </div>
        }
      </React.Fragment>
    )
  }
}
export default withShortcuts(FeedbackMenu)

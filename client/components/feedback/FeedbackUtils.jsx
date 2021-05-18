import React from 'react'

import FeedbackBlock from './FeedbackBlock.jsx'
import FeedbackBlockEdit from './FeedbackBlockEdit.jsx'

const FILTER_ICONS = {
  'no_filter': 'fa-filter',
  'required': 'fa-plus',
  'excluded': 'fa-minus'
}

const FILTER_COLORS = {
  'no_filter': '',
  'required': 'is-success',
  'excluded': 'is-danger'
}

/**
 * Adds indexes based on pre-order sorting.
 * @param root the root FO of the problem
 * @returns {*} the root FO now with index
 */
export const indexFeedbackOptions = (root) => {
  var index = 0
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
export const findFeedbackByIndex = (feedback, index) => {
  if (feedback.index === index) return feedback

  for (var i = 0; i < feedback.children.length; i++) {
    const fb = findFeedbackByIndex(feedback.children[i], index)
    if (fb !== null) return fb
  }

  return null
}

const FeedbackItem = (props) => {
  const feedbackID = props.feedback.id

  return feedbackID !== props.feedbackToEditId
    ? <FeedbackBlock
      key={'item-' + feedbackID}
      feedback={props.feedback}
      checked={props.grading && props.checkedFeedback.includes(feedbackID)}
      editFeedback={() => props.editFeedback(feedbackID, null)}
      toggleOption={props.toggleOption}
      ref={props.selectedFeedbackId === feedbackID ? props.feedbackBlock : null}
      grading={props.grading}
      selected={props.selectedFeedbackId === feedbackID || props.feedback.highlight}
      showIndex={props.showTooltips}
      filterMode={(props.grading && props.feedbackFilters[feedbackID]) || 'no_filter'}
      applyFilter={(e, newFilterMode) => props.applyFilter(e, feedbackID, newFilterMode)}
      children={props.feedback.children}
      parentProps={props} />
    : <FeedbackBlockEdit
      key={'item-' + feedbackID}
      feedback={props.feedback}
      problemID={props.problemID}
      goBack={() => props.editFeedback(0, null)}
      updateFeedback={props.updateFeedback}
      children={props.feedback.children}
      parentProps={props} />
}

export { FILTER_COLORS, FILTER_ICONS, FeedbackItem }

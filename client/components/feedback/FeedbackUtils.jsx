import React from 'react'

import FeedbackBlock from './FeedbackBlock.jsx'
import FeedbackBlockEdit from './FeedbackBlockEdit.jsx'

const FILTER_ICONS = {
  no_filter: 'fa-filter',
  required: 'fa-plus',
  excluded: 'fa-minus'
}

const FILTER_COLORS = {
  no_filter: '',
  required: 'is-success',
  excluded: 'is-danger'
}

/**
 * Adds indexes based on pre-order sorting.
 * @param root the root FO of the problem
 * @returns {*} the root FO now with index
 */
export const indexFeedbackOptions = (feedback, rootId) => {
  let index = 0
  const idStack = [rootId]
  while (idStack.length > 0) {
    const id = idStack.shift()
    feedback[id].index = index++
    idStack.unshift(...feedback[id].children)
  }
  return feedback
}

/**
 * Finds the FO that matches the given index (used for shortcuts)
 * @param feedback the list of indexed feedback options.
 * @param index the index to match
 * @returns {null|*} return null if no match, or else the matching FO
 */
export const findFeedbackByIndex = (feedback, index) => {
  return Object.values(feedback).find(fb => fb.index === index)
}

const FeedbackItem = (props) => {
  const feedbackID = props.feedbackID

  return feedbackID !== props.feedbackToEditId
    ? <FeedbackBlock
      ref={props.selectedFeedbackId === feedbackID ? props.blockRef : null}
      key={'item-' + feedbackID}
      feedback={props.indexedFeedback[feedbackID]}
      indexedFeedback={props.indexedFeedback}
      checked={props.grading && props.checkedFeedback.includes(feedbackID)}
      editFeedback={() => props.editFeedback(feedbackID, null)}
      toggleOption={props.toggleOption}
      grading={props.grading}
      selected={props.selectedFeedbackId === feedbackID || props.indexedFeedback[feedbackID].highlight}
      showIndex={props.showTooltips}
      filterMode={(props.grading && props.feedbackFilters[feedbackID]) || 'no_filter'}
      applyFilter={(e, newFilterMode) => props.applyFilter(e, feedbackID, newFilterMode)}
      exclusive={props.exclusive}
      parentProps={props} />
    : <FeedbackBlockEdit
      key={'item-' + feedbackID}
      feedback={props.indexedFeedback[feedbackID]}
      indexedFeedback={props.indexedFeedback}
      problemID={props.problemID}
      goBack={() => props.editFeedback(0, null)}
      updateFeedback={props.updateFeedback}
      parentProps={props} />
}

export { FILTER_COLORS, FILTER_ICONS, FeedbackItem }

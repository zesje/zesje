import React from 'react'

import Tooltip from '../Tooltip.jsx'
import { FILTER_COLORS, FILTER_ICONS, FeedbackList } from './FeedbackUtils.jsx'

class FeedbackBlock extends React.Component {
  toggle = () => this.props.toggleOption(this.props.feedback.id)

  editFeedback = (e) => {
    e.stopPropagation()
    this.props.editFeedback()
  }

  render () {
    const shortcut = (this.props.feedback.index < 11 ? '' : 'shift + ') + this.props.feedback.index % 10

    return (
      <li>
        <a
          className='panel-block feedback-item'
          onClick={this.props.grading ? this.toggle : this.props.editFeedback}
        >
          <span
            className={'tag is-score has-tooltip-left has-tooltip-arrow' +
              (this.props.exclusive ? ' is-circular' : ' is-squared') +
              (this.props.checked ? (this.props.valid ? ' is-link' : ' is-danger') : '') +
              ((this.props.showIndex && this.props.feedback.index <= 20)
                ? ' has-tooltip-active'
                : '')}
            data-tooltip={shortcut}>
            {this.props.feedback.score}
          </span>
          <span className='text-container'>
            {this.props.feedback.name}
          </span>
          <div className='edit-container'>
            <Tooltip button text={this.props.feedback.description} location='top' />
            <button
              className={'button is-edit is-pulled-right'}
              onClick={this.editFeedback}
            >
              <i className='fa fa-pen' />
            </button>
          </div>
          {this.props.grading &&
            <div
              className={
                // TODO: Change to is-popover-right once Firefox supports :has()
                `popover is-popover-top button is-pulled-right filter-container
                ${(this.props.filterMode === 'no_filter' ? ' no-filter' : '')}
                ${FILTER_COLORS[this.props.filterMode]}`}
            >
              <i className={`fa ${FILTER_ICONS[this.props.filterMode]}`} />
              <div className='is-filter'
                onClick={e => this.props.applyFilter(e, 'no_filter')}
              />
              <div className='popover-content' style={{ display: 'grid', gridAutoFlow: 'column', gap: '1em' }}>
                <button
                  className={
                    `button popover-trigger is-inverted is-small fa ${FILTER_ICONS.required} ${FILTER_COLORS.required}`}
                  onClick={e => this.props.applyFilter(e, 'required')}
                />
                <button
                  className={
                    `button popover-trigger is-inverted is-small fa ${FILTER_ICONS.excluded} ${FILTER_COLORS.excluded}`}
                  onClick={(e) => this.props.applyFilter(e, 'excluded')}
                />
              </div>
            </div>
          }
        </a>
        <FeedbackList {...this.props.parentProps} feedback={this.props.feedback} />
      </li>
    )
  }
}

export default FeedbackBlock

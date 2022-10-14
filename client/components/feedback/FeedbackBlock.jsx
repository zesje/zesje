import React from 'react'

import Tooltip from '../Tooltip.jsx'
import { FILTER_COLORS, FILTER_ICONS, FeedbackList } from './FeedbackUtils.jsx'

class FeedbackBlock extends React.Component {
  state = {
    hover: {
      block: false,
      edit: false,
      filter: false
    }
  }

  leave = (component) => {
    this.setState(prevState => ({
      hover: {
        ...prevState.hover,
        [component]: false
      }
    }))
  }

  enter = (component) => {
    this.setState(prevState => ({
      hover: {
        ...prevState.hover,
        [component]: true
      }
    }))
  }

  toggle = () => {
    if (!this.state.hover.edit) {
      this.props.toggleOption(this.props.feedback.id)
    }
  }

  render () {
    const shortcut = (this.props.feedback.index < 11 ? '' : 'shift + ') + this.props.feedback.index % 10

    return (
      <li>
        <a
          className='panel-block feedback-item'
          onClick={this.props.grading ? this.toggle : this.props.editFeedback}
          onMouseEnter={() => this.enter('block')} onMouseLeave={() => this.leave('block')}
        >
          <span
            style={{ width: '1.5rem', gridColumn: 1, gridRow: 1 }}
            className={'tag has-tooltip-left has-tooltip-arrow' +
              (this.props.exclusive ? ' is-circular' : ' is-squared') +
              (this.props.checked ? (this.props.valid ? ' is-link' : ' is-danger') : '') +
              ((this.props.showIndex && this.props.feedback.index <= 20)
                ? ' has-tooltip-active'
                : '')}
            data-tooltip={shortcut}>
            {this.props.feedback.score}
          </span>
          <span className={'has-text-overflow'} style={{ paddingLeft: '0.5em' }}>
            {this.props.feedback.name}
          </span>
          <div style={{ gridColumn: '3', zIndex: 8, gridRow: 1, display: this.state.hover.block ? 'flex' : 'none' }}>
          <Tooltip text={this.props.feedback.description} location='top' />
          <button
            className={'button is-pulled-right is-small is-light' +
              (this.state.hover.edit ? ' is-link' : '')}
            onMouseEnter={() => this.enter('edit')} onMouseLeave={() => this.leave('edit')}
            onClick={this.props.editFeedback}
          >
            <i className='fa fa-pen' />
          </button>
          </div>
          {this.props.grading &&
            <div
              className={
                `popover is-popover-right button is-pulled-right is-small is-light
                ${(this.props.filterMode !== 'no_filter' ? ' is-inverted' : '')}
                ${FILTER_COLORS[this.props.filterMode]}`}
              onMouseEnter={() => this.enter('filter')} onMouseLeave={() => this.leave('filter')}
              style={{
                display: !this.state.hover.block && this.props.filterMode === 'no_filter' ? 'none' : '',
                gridColumn: '4',
                zIndex: 8,
                gridRow: 1
              }}
            >
              <i className={`fa ${FILTER_ICONS[this.props.filterMode]}`} />
              <div
                style={{
                  display: this.state.hover.filter ? '' : 'none',
                  position: 'absolute',
                  left: 0,
                  top: 0,
                  width: '4em',
                  height: '4em',
                  transform: 'translateY(-25%)'
                }}
                onClick={e => this.props.applyFilter(e, 'no_filter')}
              />
              <div className='popover-content' style={{ display: 'grid', gridAutoFlow: 'row', gap: '1em' }}>
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

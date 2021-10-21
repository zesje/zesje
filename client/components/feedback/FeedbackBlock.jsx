import React from 'react'

import Tooltip from '../Tooltip.jsx'
import { FILTER_COLORS, FILTER_ICONS, FeedbackItem } from './FeedbackUtils.jsx'

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
    const children = this.props.feedback.children.map(
      (id) => <FeedbackItem {...this.props.parentProps}
        feedbackID={id} key={'child-' + id} exclusive={this.props.feedback.exclusive} />
    )
    const shortcut = (this.props.feedback.index < 11 ? '' : 'shift + ') + this.props.feedback.index % 10

    return (
      <li>
        <a
          className='panel-block feedback-item'
          onClick={this.props.grading ? this.toggle : this.props.editFeedback}
          style={this.props.selected ? { backgroundColor: '#209cee' } : {}}
          onMouseEnter={() => this.enter('block')} onMouseLeave={() => this.leave('block')}
        >
          <span
            style={{ width: '1.5rem' }}
            className={'tag has-tooltip-left has-tooltip-arrow' +
              (this.props.exclusive ? ' is-circular' : ' is-squared') +
              (this.props.checked ? ' is-link' : '') +
              ((this.props.showIndex && this.props.feedback.index <= 20)
                ? ' has-tooltip-active'
                : '')}
            data-tooltip={shortcut}>
            {this.props.feedback.score}
          </span>
          <span className={'grow'} style={{ paddingLeft: '0.5em' }}>
            {this.props.feedback.name}
            <Tooltip text={this.props.feedback.description} />
          </span>
          <button
            className={'button is-pulled-right is-small is-light' +
              (this.state.hover.block ? '' : ' is-invisible') +
              (this.state.hover.edit ? ' is-link' : '')}
            onMouseEnter={() => this.enter('edit')} onMouseLeave={() => this.leave('edit')}
            onClick={this.props.editFeedback}
          >
            <i className='fa fa-pen' />
          </button>
          {this.props.grading &&
            <div
              className={`popover is-popover-right button is-pulled-right is-small is-light
            ${(this.props.filterMode !== 'no_filter' ? 'is-inverted' : (this.state.hover.block ? '' : 'is-invisible'))}
            ${FILTER_COLORS[this.props.filterMode]}`}
              onMouseEnter={() => this.enter('filter')} onMouseLeave={() => this.leave('filter')}
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
        {children.length > 0 ? <ul className='menu-list'> {children} </ul> : null}
      </li>
    )
  }
}

export default FeedbackBlock

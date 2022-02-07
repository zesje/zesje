import React from 'react'
import SearchBox from '../../components/SearchBox.jsx'

const NavButton = (props) => {
  return (
    <div className={'control has-tooltip-arrow' + (props.showTooltips ? ' has-tooltip-active' : '')}
      data-tooltip={props.tooltip}>
      <button
        type='submit'
        className={`button ${props.style} fa ${props.faIcon}`}
        style={{ width: '4em' }}
        onClick={props.onClick}
        disabled={props.disabled} />
    </div>
  )
}

class GradeNavigation extends React.Component {
  setSubmission = (submission) => {
    this.props.setSubmission(submission.id)
  }

  render () {
    const submission = this.props.submission
    const submissions = this.props.submissions

    const cannotNavigate = submission.meta.filter_matches < 2

    return (
          <div className='field has-addons is-mobile'>
            <NavButton
              style='is-info is-rounded'
              faIcon='fa-angle-double-left'
              onClick={this.props.first}
              tooltip='shift + ←'
              showTooltips={this.props.showTooltips}
              disabled={cannotNavigate || submission.meta.no_prev_sub}
            />
            <NavButton
              style='is-link'
              faIcon='fa-angle-left'
              onClick={this.props.prev}
              tooltip='←'
              showTooltips={this.props.showTooltips}
              disabled={cannotNavigate || submission.meta.no_prev_sub}
            />
            <div
              id='search'
              className={
                'control is-expanded has-tooltip-arrow' + (this.props.showTooltips ? ' has-tooltip-active' : '')
              }
              data-tooltip={'Press ctrl to ' + (this.props.showTooltips ? 'hide' : 'show') + ' shortcuts'}
            >
              <SearchBox
                placeholder='Search for a submission'
                setSelected={this.setSubmission}
                selected={submission}
                options={submissions}
                suggestionKeys={(this.props.anonymous
                  ? ['id']
                  : [
                      'student.id',
                      'student.firstName',
                      'student.lastName',
                      'id'
                    ])}
                renderSelected={({ id, student }) => {
                  if (student && !this.props.anonymous) {
                    return `${student.firstName} ${student.lastName} (${student.id})`
                  } else {
                    return `Solution #${id}`
                  }
                }}
                renderSuggestion={({ id, student }) => {
                  if (student && !this.props.anonymous) {
                    return (
                      <div className='flex-parent'>
                        <b className='flex-child truncated'>
                          {`${student.firstName} ${student.lastName}`}
                        </b>
                        <i className='flex-child fixed'>
                          ({student.id}, #{id})
                        </i>
                      </div>
                    )
                  } else {
                    return (
                      <div className='flex-parent'>
                        <b className='flex-child fixed'>
                          Solution #{id}
                        </b>
                      </div>
                    )
                  }
                }}
              />
            </div>
            <NavButton
              style='is-link'
              faIcon='fa-angle-right'
              onClick={this.props.next}
              tooltip='→'
              showTooltips={this.props.showTooltips}
              disabled={cannotNavigate || submission.meta.no_next_sub}
            />
            <NavButton
              style='is-info is-rounded'
              faIcon='fa-angle-double-right'
              onClick={this.props.last}
              tooltip='shift + →'
              showTooltips={this.props.showTooltips}
              disabled={cannotNavigate || submission.meta.no_next_sub}
            />
          </div>
    )
  }
}

export default GradeNavigation

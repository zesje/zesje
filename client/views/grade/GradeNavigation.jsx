import React from 'react'
import SearchBox from '../../components/SearchBox.jsx'

class GradeNavigation extends React.Component {
  render () {
    const submission = this.props.submission
    const submissions = this.props.submissions

    return (
      <div className='level'>
        <div className='level-item make-wider'>
          <div className='field has-addons is-mobile'>
            <div className='control'>
              <button type='submit'
                className={'button is-info is-rounded is-hidden-mobile' +
                    (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                data-tooltip='shift + ←'
                onClick={this.props.prevUngraded}>ungraded</button>
              <button type='submit'
                className={'button is-link' +
                    (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                data-tooltip='←'
                onClick={this.props.prev}>Previous</button>
            </div>
            <div className='control is-wider'>
              <SearchBox
                placeholder='Search for a submission'
                setSelected={this.props.updateSubmission}
                selected={submission}
                options={submissions}
                suggestionKeys={(this.props.anonymous ? ['id'] : [
                  'student.id',
                  'student.firstName',
                  'student.lastName',
                  'id'
                ])}
                renderSelected={({id, student}) => {
                  if (student && !this.props.anonymous) {
                    return `${student.firstName} ${student.lastName} (${student.id})`
                  } else {
                    return `#${id}`
                  }
                }}
                renderSuggestion={({id, student}) => {
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
                        #{id}
                        </b>
                      </div>
                    )
                  }
                }}
              />
            </div>
            <div className='control'>
              <button type='submit'
                className={'button is-link' +
                    (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                data-tooltip='→'
                onClick={this.props.next}>Next</button>
              <button type='submit'
                className={'button is-info is-rounded is-hidden-mobile' +
                    (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                data-tooltip='shift + →'
                onClick={this.props.nextUngraded}>ungraded</button>
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default GradeNavigation

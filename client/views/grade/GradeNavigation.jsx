import React from 'react'
import SearchBox from '../../components/SearchBox.jsx'

class GradeNavigation extends React.Component {
  setSubmission = (submission) => {
    this.props.setSubmission(submission.id)
  }

  render () {
    const submission = this.props.submission
    const submissions = this.props.submissions

    return (
      <div className='level'>
        <div className='level-item make-wider'>
          <div className='field has-addons is-mobile'>
            <div className='control'>
              <button type='submit'
                className={'button is-link is-rounded fa fa-angle-left' +
                      (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                style={{width: '4em'}}
                data-tooltip='←'
                onClick={this.props.prev} />
            </div>
            <div id='search' className={'control is-wider ' + (this.props.showTooltips ? 'tooltip is-tooltip-active tooltip-no-arrow' : '')}
              data-tooltip='Press ctrl to hide shortcuts'>
              <SearchBox
                placeholder='Search for a submission'
                setSelected={this.setSubmission}
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
                className={'button is-link is-rounded fa fa-angle-right' +
                    (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
                style={{width: '4em'}}
                data-tooltip='→'
                onClick={this.props.next} />
            </div>
          </div>
        </div>
      </div>
    )
  }
}

export default GradeNavigation

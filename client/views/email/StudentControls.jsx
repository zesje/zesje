import React from 'react'
import Notification from 'react-bulma-notification'

import SearchBox from '../../components/SearchBox.jsx'
import * as api from '../../api.jsx'

function withoutDuplicates (items, keyFn = (x => x)) {
  let seenKeys = new Set()
  let uniqueItems = []
  for (const item of items) {
    if (!seenKeys.has(keyFn(item))) {
      uniqueItems.push(item)
      seenKeys.add(keyFn(item))
    }
  }
  return uniqueItems
}

class StudentControls extends React.Component {
  state = {
    students: []
  }

  componentWillMount () {
    this.updateStudents()
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.props.examID !== prevProps.examID) {
      this.updateStudents()
    }
  }

  updateStudents = () => {
    api.get('submissions/' + this.props.examID)
      .then(submissions => {
        // Need to de-duplicate, as some students
        const students = withoutDuplicates(
          submissions.reduce((acc, sub) => sub.validated && sub.student ? acc.concat(sub.student) : acc, []),
          student => student.id
        )
        this.setState({ students })
        this.props.setStudent(students[0] || null) // in case 'students' is empty
      })
      .catch(err => {
        console.log(err)
        this.setState({students: []})
        this.props.setStudent(null)
        Notification.error('Failed to load students.')
      })
  }

  render () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Student </div>
        <div className='panel-block'>
          {this.state.students.length > 0 ? (
            <div className='field' style={{width: '100%'}}>
              <div className='control'>
                <SearchBox
                  placeholder='Search for a student'
                  selected={this.props.selectedStudent}
                  options={this.state.students}
                  suggestionKeys={[
                    'id',
                    'firstName',
                    'lastName'
                  ]}
                  setSelected={student => {
                    this.props.setStudent(student)
                  }}
                  renderSelected={(student) => (
                    student !== null
                      ? `${student.firstName} ${student.lastName} (${student.id})`
                      : ''
                  )}
                  renderSuggestion={(student) => {
                    return <div>
                      <b>{`${student.firstName} ${student.lastName}`}</b>
                      <i style={{float: 'right'}}>({student.id})</i>
                    </div>
                  }}
                />
              </div>
            </div>
          ) : (
            <p>No submissions found for this exam.</p>
          )}
        </div>
      </div>
    )
  }
}

export default StudentControls

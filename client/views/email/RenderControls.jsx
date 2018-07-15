import React from 'react'

import * as api from '../../api.jsx'

import SearchBox from '../../components/SearchBox.jsx'

class RenderControls extends React.Component {
  state = {
    students: []
  }

  componentWillMount () {
    api
      .get('students')
      .then(students => {
        this.setState({ students })
        this.props.setStudent(students[0])
      })
  }

  render () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Render </div>
        <div className='panel-block'>
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
                setSelected={studentID => {
                  const idx = this.state.students.findIndex(s => s.id === studentID)
                  this.props.setStudent(this.state.students[idx])
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

        </div>
      </div>
    )
  }
}

export default RenderControls

import React from 'react'

import Notification from 'react-bulma-notification'
import Dropzone from 'react-dropzone'

import * as api from '../../api.jsx'

import IDBlock from './IDBlock.jsx'

const BackButton = (props) => (
  <button className='button is-light is-fullwidth' onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-chevron-left' />
    </span>
    <span>search</span>
  </button>
)

const SaveButton = (props) => (
  <button className='button is-primary is-fullwidth' disabled={props.disabled} onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-floppy-o' />
    </span>
    <span>save</span>
  </button>
)

// Windows uses vnd.ms-excel mimetype for CSV files
const UploadButton = (props) => (
  <Dropzone
    className='button is-link is-fullwidth'
    accept='text/csv,application/vnd.ms-excel'
    onDrop={props.onDrop}
    disablePreview>
    <span className='icon is-small'>
      <i className='fa fa-upload' />
    </span>
    <span>upload</span>
  </Dropzone>
)

class EditPanel extends React.Component {
  state = {
    id: '',
    firstName: '',
    lastName: '',
    email: ''
  }

  componentWillMount = () => {
    if (this.props.editStud) {
      const stud = this.props.editStud
      this.setState({
        id: stud.id,
        firstName: stud.firstName,
        lastName: stud.lastName,
        email: stud.email
      })
    }
  }

  changeFirstName = (event) => {
    this.setState({
      firstName: event.target.value
    })
  }
  changeLastName = (event) => {
    this.setState({
      lastName: event.target.value
    })
  }
  changeMail = (event) => {
    this.setState({
      email: event.target.value
    })
  }

  setID = (id, student) => {
    this.setState({
      id: id
    })

    if (student) {
      this.setState({
        firstName: student.firstName,
        lastName: student.lastName,
        email: student.email
      })
    }
  }

  saveStudent = () => {
    api.put('students', {
      studentID: this.state.id,
      firstName: this.state.firstName,
      lastName: this.state.lastName,
      email: this.state.email
    })
      .then((stud) => {
        this.setState({
          id: '',
          firstName: '',
          lastName: '',
          email: ''
        })
        if (this.props.editStud) {
          this.props.toggleEdit()
        } else {
          this.idblock.clear()
        }
      }).catch(resp => {
        resp.json().then(r => Notification.error(r.message, {
          duration: 0,
          closable: true
        }))
      })
  }

  uploadStudent = (accepted, rejected) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a CSV file')
      return
    }
    accepted.map(file => {
      const data = new window.FormData()
      data.append('csv', file)
      api.post('students', data)
        .then(resp => {
          let totalSuccess = resp.added + resp.updated + resp.identical
          let total = totalSuccess + resp.failed
          let sentences = []
          if (resp.added) sentences.push(<React.Fragment><b>{resp.added}</b> new students were added </React.Fragment>)
          if (resp.updated) sentences.push(<React.Fragment><b>{resp.updated}</b> students were updated</React.Fragment>)
          if (resp.identical) sentences.push(<React.Fragment><b>{resp.identical}</b> were already up to date</React.Fragment>)

          let sentence = sentences.map((sent, index) => (
            <React.Fragment>
              {sent}{index <= sentences.length - 3 ? ', ' : ''}{index === sentences.length - 2 ? ' and ' : ''}
            </React.Fragment>
          ))
          let message = <p>
            Succesfully processed <b>{totalSuccess} / {total}</b> students. A total of {sentence}.
          </p>
          if (resp.failed === 0) {
            Notification.success(message, { 'duration': 10, 'closeable': true })
          } else {
            message = <div className='content'>
              {message}
              <p>However, we were not able to process <b>{resp.failed}</b> students:</p>
              <ul>
                {
                  resp.errors.map((error, index) => (
                    <li key={index}>{error}</li>
                  ))
                }
              </ul>
            </div>
            Notification.warn(message, { 'duration': 0, 'closeable': true })
          }
        })
        .catch(resp => {
          console.error('failed to upload student CSV file')
          resp.json().then(r => Notification.error(r.message), { 'duration': 0, 'closeable': true })
        })
    })
  }

  render () {
    const empty = !(this.state.id + this.state.firstName + this.state.lastName + this.state.email)
    const full = this.state.id && this.state.firstName && this.state.lastName

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Manage students
        </p>
        <IDBlock setID={this.setID} editStud={this.state.id} ref={(id) => { this.idblock = id }} />

        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Name</label>
            <div className='control has-icons-left'>
              <input className='input' placeholder='First name'
                value={this.state.firstName} onChange={this.changeFirstName} />
              <span className='icon is-small is-left'>
                <i className='fa fa-quote-left' />
              </span>
            </div>

            <div className='control has-icons-left'>
              <input className='input' placeholder='Second name'
                value={this.state.lastName} onChange={this.changeLastName} />
              <span className='icon is-small is-left'>
                <i className='fa fa-quote-right' />
              </span>
            </div>

          </div>
        </div>

        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Email</label>
            <div className='control has-icons-left has-icons-right'>
              <input className='input' placeholder='Email input'
                value={this.state.email} onChange={this.changeMail} />
              <span className='icon is-small is-left'>
                <i className='fa fa-envelope' />
              </span>
            </div>
          </div>
        </div>

        <div className='panel-block'>
          <BackButton onClick={this.props.toggleEdit} />
          {empty
            ? <UploadButton onDrop={this.uploadStudent} />
            : <SaveButton disabled={!full} onClick={this.saveStudent} />
          }
        </div>
      </nav>
    )
  }
}

export default EditPanel

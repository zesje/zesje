import React from 'react'

import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'
import SearchBox from '../components/SearchBox.jsx'

import EmailControls from './email/EmailControls.jsx'

class Email extends React.Component {
  state = {
    template: '',
    templateWasModified: false,
    renderedTemplate: '',
    students: [],
    selectedStudent: null
  }

  componentWillMount () {
    api
      .get(`templates/${this.props.exam.id}`)
      .then(template => this.setState({ template }))
    api
      .get('students')
      .then(students => this.setState({
        students,
        selectedStudent: students[0]
      }))
      .then(this.renderTemplate)
  }

  renderTemplate = () => {
    if (this.state.selectedStudent === null) {
      return
    }
    return (
      api
        .post(
          `templates/rendered/${this.props.exam.id}/${this.state.selectedStudent.id}`,
          { template: this.state.template }
        )
        .then(renderedTemplate => (
          this.setState({ renderedTemplate })
        ))
    )
  }

  saveTemplate = () => {
    return api
      .put(`templates/${this.props.exam.id}`, {
        template: this.state.template
      })
      .then(() => this.setState({ templateWasModified: false }))
  }

  RenderControls = () => {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Render </div>
        <div className='panel-block'>
          <div className='field' style={{width: '100%'}}>
            <div className='control'>
              <SearchBox
                placeholder='Search for a student'
                selected={this.state.selectedStudent}
                options={this.state.students}
                suggestionKeys={[
                  'id',
                  'firstName',
                  'lastName'
                ]}
                setSelected={studentID => {
                  const idx = this.state.students.findIndex(s => s.id === studentID)
                  this.setState({
                    selectedStudent: this.state.students[idx]
                  }, this.renderTemplate)
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

  TemplateControls = () => {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Template </div>
        <div className='panel-block'>
          <button
            className='button is-success is-fullwidth'
            disabled={!this.state.templateWasModified}
            onClick={this.saveTemplate}
          >
            Save
          </button>
        </div>
      </div>
    )
  }

  TemplateEditor = () => {
    return (
      <textarea
        className='textarea'
        style={{height: '100%'}}
        value={this.state.template}
        onChange={evt => (
          this.setState({
            template: evt.target.value,
            templateWasModified: true
          })
        )}
        onBlur={this.renderTemplate}
      />
    )
  }

  RenderedTemplate = () => {
    return (
      <textarea
        className='textarea is-unselectable has-background-light'
        style={{height: '100%', borderColor: '#fff'}}
        value={this.state.renderedTemplate}
        readOnly
      />
    )
  }

  render () {
    return (
      <React.Fragment>
        <Hero title='Email' subtitle='So the students get their feedback' />
        <section className='section'>
          <div className='container'>
            <div className='columns is-tablet'>
              <div className='column is-3-tablet'>
                <this.TemplateControls />
                <this.RenderControls />
                <EmailControls
                  exam={this.props.exam}
                  student={this.state.selectedStudent}
                />
              </div>
              <div className='column'>
                <this.TemplateEditor />
              </div>
              <div className='column'>
                <this.RenderedTemplate />
              </div>
            </div>
          </div>
        </section>
      </React.Fragment>
    )
  }
}

export default Email

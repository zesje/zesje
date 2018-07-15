import React from 'react'

import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'

import EmailControls from './email/EmailControls.jsx'
import StudentControls from './email/StudentControls.jsx'

class Email extends React.Component {
  state = {
    template: '',
    templateWasModified: false,
    renderedTemplate: '',
    selectedStudent: null
  }

  componentWillMount () {
    api
      .get(`templates/${this.props.exam.id}`)
      .then(template => this.setState({ template }))
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
                <StudentControls
                  selectedStudent={this.state.selectedStudent}
                  setStudent={student => {
                    this.setState({
                      selectedStudent: student
                    }, this.renderTemplate)
                  }}
                />
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

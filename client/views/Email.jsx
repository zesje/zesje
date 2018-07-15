import React from 'react'

import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'

import EmailControls from './email/EmailControls.jsx'
import StudentControls from './email/StudentControls.jsx'
import TemplateEditor from './email/TemplateEditor.jsx'

class Email extends React.Component {
  state = {
    template: null,
    templateWasModified: false,
    selectedStudent: null
  }

  componentWillMount () {
    api
      .get(`templates/${this.props.exam.id}`)
      .then(template => this.setState({ template }))
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

              <TemplateEditor
                exam={this.props.exam}
                student={this.state.selectedStudent}
                template={this.state.template}
                onTemplateChange={template => {
                  this.setState({
                    template,
                    templateWasModified: true
                  })
                }}
              />
            </div>
          </div>
        </section>
      </React.Fragment>
    )
  }
}

export default Email

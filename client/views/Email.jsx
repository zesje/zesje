import React from 'react'

import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'

import EmailControls from './email/EmailControls.jsx'
import StudentControls from './email/StudentControls.jsx'
import TemplateControls from './email/TemplateControls.jsx'
import TemplateEditor from './email/TemplateEditor.jsx'

class Email extends React.Component {
  state = {
    template: null,
    selectedStudent: null
  }

  componentWillMount () {
    api
      .get(`templates/${this.props.exam.id}`)
      .then(template => this.setState({ template }))
  }

  render () {
    return (
      <React.Fragment>
        <Hero title='Email' subtitle='So the students get their feedback' />
        <section className='section'>
          <div className='container'>
            <div className='columns is-tablet'>
              <div className='column is-3-tablet'>
                <TemplateControls
                  exam={this.props.exam}
                  template={this.state.template}
                />
                <StudentControls
                  exam={this.props.exam}
                  selectedStudent={this.state.selectedStudent}
                  setStudent={student => {
                    this.setState({
                      selectedStudent: student
                    }, () => student && this.renderTemplate())
                  }}
                />
                <EmailControls
                  template={this.state.template}
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
                    template
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

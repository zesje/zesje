import React from 'react'

import Fail from './Fail.jsx'
import * as api from '../api.jsx'

import EmailControls from './email/EmailControls.jsx'
import StudentControls from './email/StudentControls.jsx'
import TemplateControls from './email/TemplateControls.jsx'
import TemplateEditor from './email/TemplateEditor.jsx'

class Email extends React.Component {
  state = {
    template: null,
    selectedStudent: null,
    error: null
  }

  constructor (props) {
    super(props)
    this.loadTemplate()
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.props.examID !== prevProps.examID) {
      this.loadTemplate()
    }
  }

  loadTemplate = () => {
    api
      .get(`templates/${this.props.examID}`)
      .then(template => this.setState({ template }))
      .catch(err => {
        console.log(err)
        err.json().then(e => {
          if (e.status === 404) {
            this.setState({ error: e.message })
          }
        })
      })
  }

  render () {
    // This should happen when the exam does not exist.
    if (this.state.error) {
      return <Fail message={this.state.error} />
    }

    return (
      <>
            <div className='columns is-tablet'>
              <div className='column is-3-tablet'>
                <TemplateControls
                  examID={this.props.examID}
                  template={this.state.template}
                />
                <StudentControls
                  examID={this.props.examID}
                  selectedStudent={this.state.selectedStudent}
                  setStudent={student => {
                    this.setState({
                      selectedStudent: student
                    })
                  }}
                />
                <EmailControls
                  template={this.state.template}
                  examID={this.props.examID}
                  student={this.state.selectedStudent}
                />
              </div>

              <TemplateEditor
                examID={this.props.examID}
                student={this.state.selectedStudent}
                template={this.state.template}
                onTemplateChange={template => {
                  this.setState({
                    template
                  })
                }}
              />
            </div>
      </>
    )
  }
}

export default Email

import React from 'react'

import { toast } from 'bulma-toast'

import * as api from '../../api.jsx'

import TabbedPanel from '../../components/TabbedPanel.jsx'
import ConfirmationButton from '../../components/ConfirmationButton.jsx'

const AttachPDF = (props) => (
  <div className='field'>
    <div className='control'>
      <label className='checkbox'>
        <input
          type='checkbox'
          checked={props.attachPDF}
          onChange={(evt) => props.onChecked(evt.target.checked)}
          disabled={props.disabled}
        />
        Attach PDF
      </label>
    </div>
  </div>
)

const ToField = (props) => (
  <div className='field has-addons'>
    <div className='control'>
      <a className='button is-static'>to :</a>
    </div>
    <div className='control is-expanded'>
      <input
        className='input is-static'
        type='email'
        value={props.email}
        readOnly
        style={{paddingLeft: 'calc(0.625em - 1px)'}}
      />
    </div>
  </div>
)

const CCField = (props) => (
  <div className='field has-addons'>
    <div className='control'>
      <a className='button is-static'>cc :</a>
    </div>
    <div className='control is-expanded'>
      <input
        className='input'
        type='email'
        placeholder='course-instructor@tudelft.nl'
        value={props.email || ''}
        onChange={evt => props.onChange(evt.target.value)}
        disabled={props.disabled}
      />
    </div>
  </div>
)

const SendButton = (props) => (
  <button
    className={
      'button is-primary is-fullwidth ' +
      (props.sending ? 'is-loading' : null)
    }
    onClick={props.onSend}
    disabled={props.disabled}
  >
    Send
  </button>
)

const SendWithConfirmationButton = (props) => (
  <ConfirmationButton
    className={
      'button is-primary is-fullwidth ' +
      (props.sending ? 'is-loading' : null)
    }
    confirmationText={'Email all students who took this exam?'}
    contentText={'This may take some time.'}
    onConfirm={props.onSend}
    disabled={props.disabled}
  >
    Send
  </ConfirmationButton>
)

class EmailIndividualControls extends React.Component {
  state = {
    attachPDF: true,
    copyTo: null,
    sending: false
  }

  sendEmail = async () => {
    this.setState({ sending: true })
    try {
      await api.post(
        `email/${this.props.examID}/${this.props.student.id}`,
        {
          template: this.props.template,
          attach: this.state.attachPDF,
          copy_to: this.state.copyTo
        }
      )
      toast({ message: `Sent email to ${this.props.student.email}`, type: 'is-success' })
      return
    } catch (error) {
      try {
        const resp = await error.json()
        toast({ message: resp.message, duration: 3000, type: 'is-danger' })
      } catch (error) {
        // If we get here there is a bug in the backend
        toast({ message: `Failed to send email to ${this.props.student.email}`, type: 'is-danger' })
      }
    } finally {
      this.setState({ sending: false })
    }
  }

  render () {
    let p = this.props
    let email = ''
    let disabled = true
    if (p.student !== null) {
      disabled = p.student.email === null || p.template === null
      email = p.student.email || '<no email provided>'
    }
    return (
      <div
        style={{width: '100%'}}
      >
        <ToField email={email} />
        <CCField
          email={this.state.copyTo}
          onChange={copyTo => this.setState({ copyTo: copyTo || null })}
          disabled={this.state.sending}
        />
        <AttachPDF
          attachPDF={this.state.attachPDF}
          onChecked={attachPDF => this.setState({ attachPDF })}
          disabled={this.state.sending}
        />
        <SendButton
          sending={this.state.sending}
          onSend={this.sendEmail}
          disabled={disabled}
        />
      </div>
    )
  }
}

class EmailEveryoneControls extends React.Component {
  state = {
    attachPDF: true,
    sending: false
  }

  disableAnonymousMode = () => {
    api.put(`exams/${this.props.examID}`, {grade_anonymous: false}).then(resp => {
      if (resp.changed) {
        Notification.info(
          <div>
            <p>
              'Turned off anonymous grading for this exam'
            </p>
            <a onClick={() => api.put(`exams/${this.props.examID}`, {grade_anonymous: true})}>
              (undo)
            </a>
          </div>
        )
      }
    })
  }

  sendEmail = async () => {
    this.setState({ sending: true })
    try {
      const response = await api.post(
        `email/${this.props.examID}`,
        {
          template: this.props.template,
          attach: this.state.attachPDF
        }
      )
      if (response.status === 200) {
        toast({
          message: 'Sent emails to all students',
          duration: 60000,
          type: 'is-success'
        })
      } else if (response.status === 206) {
        toast({ message: `Sent emails to ${response.sent.length} students`, type: 'is-success' })
        if (response.failed_to_send.length > 0) {
          toast({
            message: 'Failed to send to the following students: ' + response.failed_to_send.join(', '),
            duration: 60000,
            type: 'is-danger'
          })
        }
        if (response.failed_to_build.length > 0) {
          toast({
            message: 'The following students have no email address specified: ' + response.failed_to_build.join(', '),
            duration: 60000,
            type: 'is-danger'
          })
        }
      }
    } catch (error) {
      try {
        let response = await error.json()
        if (response.status === 400 ||
            response.status === 409) {
          toast({ message: 'No emails sent: ' + response.message, duration: 60000, type: 'is-danger' })
        } else if (response.status === 500) {
          toast({ message: `Sent email to ${this.props.student.email}`, type: 'is-success' })
        }
      } catch (error) {
        // If we get here there is a bug in the backend
        toast({ message: 'Failed to send emails', duration: 60000, type: 'is-danger' })
      }
    } finally {
      this.setState({ sending: false })
      this.disableAnonymousMode()
    }
  }

  render () {
    let disabled = this.props.template === null
    return (
      <div style={{width: '100%'}}>
        <AttachPDF
          attachPDF={this.state.attachPDF}
          onChecked={attachPDF => this.setState({ attachPDF })}
          disabled={this.state.sending}
        />
        <SendWithConfirmationButton
          sending={this.state.sending}
          onSend={this.sendEmail}
          disabled={disabled}
        />
      </div>
    )
  }
}

class EmailControls extends React.Component {
  render () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Email </div>
        <TabbedPanel
          panels={[
            {
              name: 'Individual',
              panel: (
                <EmailIndividualControls
                  examID={this.props.examID}
                  student={this.props.student}
                  template={this.props.template}
                />
              )
            },
            {
              name: 'Everyone',
              panel: (
                <EmailEveryoneControls
                  examID={this.props.examID}
                  template={this.props.template}
                />
              )
            }
          ]}
        />
      </div>
    )
  }
}

export default EmailControls

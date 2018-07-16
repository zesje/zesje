import React from 'react'

import Notification from 'react-bulma-notification'

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
    confirmationText={'You are about to email all the students on the course'}
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
        `email/${this.props.exam.id}/${this.props.student.id}`,
        {
          template: this.props.template,
          attach: this.state.attachPDF
        }
      )
      Notification.success(`Sent email to ${this.props.student.email}`)
    } catch (response) {
      let error = response.status === 400 ? (await response.json()).message : ''
      Notification.error(
        `Failed to send email to ${this.props.student.email}: ${error}`
      )
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

  sendEmail = async () => {
    this.setState({ sending: true })
    try {
      await api.post(
        `email/${this.props.exam.id}`,
        {
          template: this.props.template,
          attach: this.state.attachPDF
        }
      )
      Notification.success(`Sent emails to everybody`)
    } catch (response) {
      let error = response.status === 400 ? (await response.json()).message : ''
      Notification.error(
        `Failed to send email to everybody: ${error}`
      )
    } finally {
      this.setState({ sending: false })
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
                  exam={this.props.exam}
                  student={this.props.student}
                  template={this.props.template}
                />
              )
            },
            {
              name: 'Everyone',
              panel: (
                <EmailEveryoneControls
                  exam={this.props.exam}
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

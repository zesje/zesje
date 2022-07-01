import React from 'react'
import ReactDOMServer from 'react-dom/server'

import { toast } from 'bulma-toast'

import * as api from '../../api.jsx'

import TabbedPanel from '../../components/TabbedPanel.jsx'
import ConfirmationButton from '../../components/modals/ConfirmationButton.jsx'
import ProgressModal from '../../components/modals/ProgressModal.jsx'

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
        style={{ paddingLeft: 'calc(0.625em - 1px)' }}
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
    confirmationText='Email all students who took this exam?'
    contentText='This may take some time.'
    onConfirm={props.onSend}
    disabled={props.disabled}
  >
    Send
  </ConfirmationButton>
)

class EmailIndividualControls extends React.Component {
  state = {
    attachPDF: true,
    copyTo: null
  }

  render () {
    const p = this.props
    let email = ''
    let disabled = true
    if (p.student !== null) {
      disabled = p.student.email === null || p.template === null
      email = p.student.email || '<no email provided>'
    }
    return (
      <div
        style={{ width: '100%' }}
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
          disabled={this.props.sending}
        />
        <SendButton
          sending={this.props.sending}
          onSend={() => this.props.sendEmail(this.props.student.id, this.state.attachPDF, this.state.copyTo)}
          disabled={disabled}
        />
      </div>
    )
  }
}

class EmailEveryoneControls extends React.Component {
  state = {
    attachPDF: true
  }

  render () {
    const disabled = this.props.template === null
    return (
      <div style={{ width: '100%' }}>
        <AttachPDF
          attachPDF={this.state.attachPDF}
          onChecked={attachPDF => this.setState({ attachPDF })}
          disabled={this.props.sending}
        />
        <SendWithConfirmationButton
          sending={this.props.sending}
          onSend={() => this.props.sendEmail(null, this.state.attachPDF)}
          disabled={disabled}
        />
      </div>
    )
  }
}

class EmailControls extends React.Component {
  state = {
    sending: false,
    failed: null
  }

  disableAnonymousMode = () => {
    api.put(`exams/${this.props.examID}`, { grade_anonymous: false }).then(resp => {
      if (resp.changed) {
        const msg = (
          <div>
            <p>Turned off anonymous grading for this exam</p>
            <a onClick={() => api.put(`exams/${this.props.examID}`, { grade_anonymous: true })}>
              (undo)
            </a>
          </div>
        )
        toast({
          message: ReactDOMServer.renderToString(msg),
          type: 'is-info'
        })
      }
    })
  }

  sendEmail = async (studentID = null, attachPDF = false, copyTo = null) => {
    this.setState({ sending: true, failed: null })

    let url = `email/${this.props.examID}`
    if (studentID != null) {
      url += `/${studentID}`
    }

    api.post(url, {
      template: this.props.template,
      attach: attachPDF,
      copy_to: copyTo
    }).then(resp => {
      if (resp.status === 200) {
        this.setState({ sending: false })
        toast({
          message: 'Emails sent to all students',
          type: 'is-success'
        })
      } else if (resp.status === 206) {
        this.setState({ sending: false, failed: resp.failed })
        toast({ message: `Sent emails to ${resp.sent.length} students`, type: 'is-warning' })
      }
    }).catch(e => {
      console.log(e)
      e.json().then(error => {
        this.setState({ sending: false, failed: error.failed })
        toast({ message: error.message, duration: 10000, type: 'is-danger' })
      })
    })

    if (studentID == null) {
      this.disableAnonymousMode()
    }
  }

  render () {
    return <>
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
                  sendEmail={this.sendEmail}
                />
              )
            },
            {
              name: 'Everyone',
              panel: (
                <EmailEveryoneControls
                  examID={this.props.examID}
                  template={this.props.template}
                  sendEmail={this.sendEmail}
                />
              )
            }
          ]}
        />
      </div>
      <ProgressModal
        active={this.state.sending}
        headerText='Sending emails...'
      />
      <div className={'modal ' + (this.state.failed != null ? 'is-active' : '')}>
        <div className='modal-background' onClick={() => this.setState({ failed: null })} />
        <div className='modal-card'>
          <header className='modal-card-head'>
            <p className='modal-card-title'>{'Failed email status'}</p>
          </header>
          <section className='modal-card-body'>
            <ul>
              {this.state.failed && this.state.failed.map(data =>
                <li key={data.studentID}>
                  <b>#{data.studentID}</b>: ({data.status}) {data.message}
                </li>
              )}
            </ul>
          </section>
        </div>
        <button className='modal-close is-large' aria-label='close' />
      </div>
    </>
  }
}

export default EmailControls

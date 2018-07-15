import React from 'react'

import * as api from '../../api.jsx'

import TabbedPanel from '../../components/TabbedPanel.jsx'

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

class EmailIndividualControls extends React.Component {
  state = {
    attachPDF: true,
    copyTo: null,
    sending: false
  }

  sendEmail = () => {
    this.setState({ sending: true })
    api
      .post(
        `email/${this.props.exam.id}/${this.props.student.id}`,
        {
          template: this.props.template,
          attach: this.state.attachPDF
        }
      )
      .finally(() => this.setState({ sending: false }))
  }

  render () {
    let email = ''
    let disabled = true
    if (this.props.student !== null) {
      disabled = this.props.student.email === null
      email = this.props.student.email || '<no email provided>'
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
    attachPDF: true
  }

  render () {
    return (
      <div style={{width: '100%'}}>
        <AttachPDF
          attachPDF={this.state.attachPDF}
          onChecked={attachPDF => this.setState({ attachPDF })}
        />
        <button
          className='button is-primary is-fullwidth'
        >
          Send
        </button>
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

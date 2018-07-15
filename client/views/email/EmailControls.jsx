import React from 'react'

import TabbedPanel from '../../components/TabbedPanel.jsx'

const AttachPDF = (props) => (
  <div className='field'>
    <div className='control'>
      <label className='checkbox'>
        <input
          type='checkbox'
          checked={props.attachPDF}
          onChange={(evt) => props.onChecked(evt.target.checked)}
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
      />
    </div>
  </div>
)

class EmailControls extends React.Component {
  state = {
    attachPDF: true,
  }

  EmailIndividualControls = () => {
    let email = ''
    let disabled = true
    if (this.props.student === null) {
      disabled = true
      email = ''
    } else if (!this.props.student.email) {
      disabled = true
      email = '<no email provided>'
    } else {
      disabled = false
      email = this.props.student.email
    }
    return (
      <div style={{width: '100%'}}>
        <ToField email={email} />
        <CCField />
        <AttachPDF
          attachPDF={this.state.attachPDF}
          onChecked={attachPDF => this.setState({ attachPDF })}
        />
        <button
          className='button is-primary is-fullwidth'
          disabled={disabled}
        >
          Send
        </button>
      </div>
    )
  }

  EmailEveryoneControls = () => {
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

  render () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Email </div>
        <TabbedPanel
          panels={[
            {
              name: 'Individual',
              panel: <this.EmailIndividualControls />
            },
            {
              name: 'Everyone',
              panel: <this.EmailEveryoneControls />
            }
          ]}
        />
      </div>
    )
  }
}

export default EmailControls

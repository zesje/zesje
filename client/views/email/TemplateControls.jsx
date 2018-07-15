import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

const templateSaveError = message => (
  Notification.error(
    `Unable to save template: ${message || ''}`,
    {
      duration: 3
    }
  )
)

class TemplateControls extends React.Component {
  state = {
    templateWasModified: false
  }

  componentWillReceiveProps (nextProps) {
    // the template is initially null, and when we first load the template
    // we is in an unmodified state.
    this.setState({
      templateWasModified: (nextProps.template !== this.props.template &&
                            this.props.template !== null)
    })
  }

  saveTemplate = async () => {
    try {
      await api.put(
        `templates/${this.props.exam.id}`,
        { template: this.props.template }
      )
      Notification.success('Template saved')
      this.setState({ templateWasModified: false })
    } catch (response) {
      if (response.status === 400) {
        let error = await response.json()
        templateSaveError(error.message)
      } else {
        templateSaveError()
      }
    }
  }

  render () {
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
}

export default TemplateControls

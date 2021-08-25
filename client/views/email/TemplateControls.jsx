import React from 'react'

import { toast } from 'bulma-toast'

import * as api from '../../api.jsx'

const templateSaveError = message => (
  toast({
    message: message || 'Unable to save template',
    duration: 3000,
    type: 'is-danger'
  })
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
        `templates/${this.props.examID}`,
        { template: this.props.template }
      )
      toast({ message: 'Template saved', type: 'is-success' })
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
            className='button is-primary is-fullwidth'
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

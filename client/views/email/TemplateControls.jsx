import React from 'react'

import * as api from '../../api.jsx'

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

  saveTemplate = () => {
    return api
      .put(`templates/${this.props.exam.id}`, {
        template: this.props.template
      })
      .then(() => this.setState({ templateWasModified: false }))
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

import React from 'react'

import Notification from 'react-bulma-notification'

import * as api from '../../api.jsx'

const renderTemplate = async (props) => {
  if (props.student === null) {
    throw new Error('No student selected')
  }
  return api
    .post(
      `templates/rendered/${props.examID}/${props.student.id}`,
      { template: props.template }
    )
}

const templateRenderError = message => (
  Notification.error(
    message || 'Unable to render template',
    {
      duration: 3
    }
  )
)

const LoadingView = () => (
  <div
    className='box has-background-light'
    style={{ height: '100%', display: 'flex', justifyContent: 'center' }}
  >
    <div
      className='has-text centered has-text-grey-light'
      style={{ alignSelf: 'center' }}
    >
      <p className='icon is-large'>
        <i className='fa fa-code fa-3x' />
      </p>
    </div>
  </div>
)

class TemplateEditor extends React.Component {
  state = {
    renderedTemplate: null
  }

  updateRenderedTemplate = async (props) => {
    try {
      let renderedTemplate = await renderTemplate(props)
      this.setState({ renderedTemplate })
    } catch (response) {
      if (response.status === 400) {
        let error = await response.json()
        templateRenderError(error.message)
      } else {
        templateRenderError()
      }
    }
  }

  componentWillReceiveProps (nextProps) {
    const isInitialized = (
      this.props.student !== null &&
      this.props.template !== null
    )
    const willBeInitialized = (
      nextProps.student !== null &&
      nextProps.template !== null
    )

    if (!isInitialized && willBeInitialized) {
      this.updateRenderedTemplate(nextProps)
    } else if (isInitialized &&
               nextProps.student.id !== this.props.student.id) {
      // Note that we only re-render here whenever the *student* changes.
      // Updates to the template itself only trigger a re-render for 'onblur'
      this.updateRenderedTemplate(nextProps)
    }
  }

  TemplateEditor = () => {
    // We call 'onTemplateChange' on every keystroke, as the container
    // needs to detect whenever anything changes, however we only re-render
    // due to template changes when we click away (blur) the template editor.
    return (
      <textarea
        className='textarea'
        style={{height: '100%'}}
        value={this.props.template || ''}
        onChange={evt => this.props.onTemplateChange(evt.target.value)}
        onBlur={() => this.updateRenderedTemplate(this.props)}
      />
    )
  }

  RenderedTemplate = () => {
    return (
      <textarea
        className='textarea is-unselectable has-background-light'
        style={{height: '100%', borderColor: '#fff'}}
        value={this.state.renderedTemplate || ''}
        readOnly
      />
    )
  }

  render () {
    return (
      <React.Fragment>
        <div className='column'>
          {
            this.props.template === null
              ? <LoadingView />
              : <this.TemplateEditor />
          }
        </div>
        <div className='column'>
          {
            this.props.student === null || this.props.template === null
              ? <LoadingView />
              : <this.RenderedTemplate />
          }
        </div>
      </React.Fragment>
    )
  }
}

export default TemplateEditor

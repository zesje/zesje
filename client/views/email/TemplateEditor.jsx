import React from 'react'

import { toast } from 'bulma-toast'

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
  toast({
    message: message || 'Unable to render template',
    duration: 10000,
    type: 'is-danger'
  })
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
      const renderedTemplate = await renderTemplate(props)
      this.setState({ renderedTemplate })
    } catch (error) {
      if (error.status === 400) {
        templateRenderError(error.message)
      } else {
        templateRenderError()
      }
    }
  }

  componentDidUpdate = (prevProps, prevState) => {
    const isInitialized = prevProps.student !== null && prevProps.template !== null
    const willBeInitialized = this.props.student !== null && this.props.template !== null

    if (!isInitialized && willBeInitialized) {
      this.updateRenderedTemplate(this.props)
    } else if (isInitialized && this.props.student.id !== prevProps.student.id) {
      // Note that we only re-render here whenever the *student* changes.
      // Updates to the template itself only trigger a re-render for 'onblur'
      this.updateRenderedTemplate(this.props)
    }
  }

  render () {
    return (
      <>
        <div className='column'>
          {
            this.props.template === null
              ? <LoadingView />
              : (
                // We call 'onTemplateChange' on every keystroke, as the container
                // needs to detect whenever anything changes, however we only re-render
                // due to template changes when we click away (blur) the template editor.
                <textarea
                  className='textarea'
                  style={{ height: '100%' }}
                  value={this.props.template || ''}
                  onChange={evt => this.props.onTemplateChange(evt.target.value)}
                  onBlur={() => this.updateRenderedTemplate(this.props)}
                />
                )
          }
        </div>
        <div className='column'>
          {
            this.props.student === null || this.props.template === null
              ? <LoadingView />
              : (
                <textarea
                  className='textarea is-unselectable has-background-light'
                  style={{ height: '100%', borderColor: '#fff' }}
                  value={this.state.renderedTemplate || ''}
                  readOnly
                />
                )
          }
        </div>
      </>
    )
  }
}

export default TemplateEditor

import React from 'react'

import * as api from '../../api.jsx'

const renderTemplate = props => {
  if (props.student === null) {
    return Promise.reject(new Error('No student selected'))
  }
  return api
    .post(
      `templates/rendered/${props.exam.id}/${props.student.id}`,
      { template: props.template }
    )
}

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

  componentWillReceiveProps (nextProps) {
    if (nextProps.student === null) {
      return
    }
    if (this.props.student === null ||
        nextProps.student.id !== this.props.student.id) {
      renderTemplate(nextProps)
        .then(renderedTemplate =>
          this.setState({ renderedTemplate })
        )
    }
  }

  TemplateEditor = () => {
    return (
      <textarea
        className='textarea'
        style={{height: '100%'}}
        value={this.props.template || ''}
        onChange={evt => this.props.onTemplateChange(evt.target.value)}
        onBlur={() => (
          renderTemplate(this.props)
            .then(renderedTemplate =>
              this.setState({ renderedTemplate })
            )
        )}
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

import React from 'react'

import Hero from '../components/Hero.jsx'

class TabbedPanel extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      selected: 0
    }
  }

  render () {
    return (
      <React.Fragment>
        <div className='panel-tabs'>
          {
            this.props.panels.map((panel, i) => (
              <a
                key={i}
                className={i === this.state.selected ? 'is-active' : ''}
                onClick={() => this.setState({ selected: i })}
              >
                {panel.name}
              </a>
            ))
          }
        </div>
        <div className='panel-block'>
          {this.props.panels[this.state.selected].panel}
        </div>
      </React.Fragment>
    )
  }
}

class Email extends React.Component {
  constructor (props) {
    super(props)

    this.EmailControls = this.EmailControls.bind(this)
    this.EmailIndividualControls = this.EmailIndividualControls.bind(this)
    this.EmailEveryoneControls = this.EmailEveryoneControls.bind(this)
    this.RenderControls = this.RenderControls.bind(this)
    this.TemplateControls = this.TemplateControls.bind(this)
    this.TemplateEditor = this.TemplateEditor.bind(this)

  }

  EmailIndividualControls () {
    return (
      <div style={{width: '100%'}}>
        <div className='field has-addons'>
          <div className='control'>
            <a className='button is-static'>to :</a>
          </div>
          <div className='control is-expanded'>
            <input
              className='input is-static'
              type='email'
              value='student@tudelft.nl'
              style={{paddingLeft: 'calc(0.625em - 1px)'}}
            />
          </div>
        </div>
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
        <div className='field'>
          <div className='control'>
            <label className='checkbox'>
              <input type='checkbox' checked/>
              Attach PDF
            </label>
          </div>
        </div>
        <button className='button is-primary is-fullwidth'>Send</button>
      </div>
    )
  }

  EmailEveryoneControls () {
    return (
      <div style={{width: '100%'}}>
        <div className='field'>
          <div className='control'>
            <label className='checkbox'>
              <input type='checkbox' checked/>
              Attach PDF
            </label>
          </div>
        </div>
        <button className='button is-primary is-fullwidth'>Send</button>

      </div>
    )
  }

  EmailControls () {
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

  RenderControls () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Render </div>
        <div className='panel-block'>
          <div className='field' style={{width: '100%'}}>
            <div className='control'>
              <input className='input' type='text' placeholder='student' />
            </div>
          </div>

        </div>
      </div>
    )
  }

  TemplateControls () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Template </div>
        <div className='panel-block'>
          <button className='button is-success is-fullwidth' disabled>
            Save
          </button>
        </div>
      </div>
    )
  }

  TemplateEditor () {
    return (
      <textarea
        className='textarea'
        style={{height: '100%'}}
        placeholder='e.g. Hello world'
      />
    )
  }

  RenderedTemplate () {
    return (
      <div
        className='box has-background-light'
        style={{height: '100%', display: 'flex', justifyContent: 'center'}}
      >
        <div className='has-text-centered has-text-grey-light' style={{alignSelf: 'center'}}>
          <p className='icon is-large' >
            <i className='fa fa-code fa-3x' />
          </p>
          <p>Select a student to render the template</p>
        </div>

      </div>
    )
  }

  render () {
    return (
      <React.Fragment>
        <Hero title='Email' subtitle='So the students get their feedback' />
        <section className='section'>
          <div className='container'>
            <div className='columns is-tablet'>
              <div className='column is-3-tablet'>
                <this.TemplateControls />
                <this.RenderControls />
                <this.EmailControls />
              </div>
              <div className='column'>
                <this.TemplateEditor />
              </div>
              <div className='column'>
                <this.RenderedTemplate />
              </div>
            </div>
          </div>
        </section>
      </React.Fragment>
    )
  }
}

export default Email

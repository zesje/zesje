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

  EmailControls () {
    return (
      <div className='panel'>
        <div className='panel-heading has-text-centered'> Email </div>
        <TabbedPanel
          panels={[
            {
              name: 'Individual',
              panel: (
                <div style={{width: '100%'}}>
                  <div className='field'>
                    <div className='control'>
                      <input
                        className='input'
                        type='text'
                        placeholder='course-instructor@tudelft.nl'
                      />
                    </div>
                  </div>
                  <div className='field'>
                    <div className='control'>
                      <label className='checkbox'>
                        <input type='checkbox' />
                        Attach PDF
                      </label>
                    </div>
                  </div>
                  <div className='field'>
                    <div className='control'>
                      <label className='checkbox'>
                        <input type='checkbox' />
                        Also send to student
                      </label>
                    </div>
                  </div>

                  <button className='button is-primary is-fullwidth'>Send</button>

                </div>
              )
            },
            {
              name: 'Everyone',
              panel: <button className='button is-danger is-fullwidth' disabled>Send</button>
            }
          ]}
        />
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
            <div className='columns is-desktop'>
              <div className='column is-3-desktop'>
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

import React from 'react'

import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'

import * as api from '../api.jsx'

class Graders extends React.Component {
  state = {
    graders: [],
    oauth_id: '',
    oauth_provider: '',
    oauth_id_field: ''
  }

  componentDidMount = () => {
    api.get('oauth/start').then(response => {
      this.setState({
        oauth_id_field: response.oauth_id_field,
        oauth_provider: response.provider
      })
    })

    api.get('graders')
      .then(graders => {
        this.setState({ graders: graders })
      })
      .catch(resp => {
        Notification.error('Could not fetch graders (see Javascript console for details)')
        console.error('Error fetching graders:', resp)
      })
  }

  changeIdField = (event) => {
    this.setState({ oauth_id: event.target.value })
  }

  submitName = (event) => {
    api.post('graders', { oauth_id: this.state.oauth_id })
      .then(graders => {
        this.setState({
          oauth_id: '',
          graders: graders
        })
      })
      .catch(resp => {
        resp.json().then(e => {
          Notification.error(e.message)
        })
        console.error('Error saving grader:', resp)
      })

    event.preventDefault()
  }

  render () {
    const idField = this.state.oauth_id_field
    const provider = this.state.oauth_provider

    return (

      <div>

        <Hero title='Manage Graders' subtitle='Many hands make light work' />

        <section className='section'>
          <div className='container'>
            <form onSubmit={this.submitName}>
              <div className='field has-addons'>
                <div className='control'>
                  <input className='input'
                    name='first_name' value={this.state.oauth_id}
                    onChange={this.changeIdField} type='text'
                    maxLength={100} placeholder={provider + ' ' + idField} />
                </div>
                <div className='control'>
                  <button type='submit' className='button is-info'>
                    <span className='icon'>
                      <i className='fa fa-plus' />
                    </span>
                    <span>Add</span>
                  </button>
                </div>
              </div>
              <p>This instance of Zesje is configured to use {idField} for authentication.
                To allow a grader to log in using {provider}, please add their {idField}.</p>
            </form>
            <br />

            <aside className='menu'>
              <p className='menu-label'>
                Added graders
              </p>
              <ul className='menu-list'>
                {this.state.graders.map((grader) =>
                  <li key={grader.id}>{grader.name ? grader.name : 'Never logged in'} - {grader.oauth_id}</li>
                )}
              </ul>
            </aside>
          </div>
        </section>

      </div>

    )
  }
}

export default Graders

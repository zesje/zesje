import React from 'react'

import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'

import * as api from '../api.jsx'

class Graders extends React.Component {
  state = {
    graders: [],
    oauth_id_field: ''
  };

  changeIdField = (event) => {
    this.setState({ oauth_id_field: event.target.value })
  }

  submitName = (event) => {
    api.post('graders', { oauth_id: this.state.oauth_id_field })
      .then(graders => {
        this.setState({
          oauth_id_field: '',
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

  componentDidMount = () => {
    api.get('graders')
      .then(graders => {
        this.setState({ graders: graders })
        console.log(graders)
      })
      .catch(resp => {
        Notification.error('could not fetch graders (see Javascript console for details)')
        console.error('Error fetching graders:', resp)
      })
  }

  render () {
    const idField = window.sessionStorage.getItem('oauth_id_field')
    const provider = window.sessionStorage.getItem('oauth_provider')

    return (

      <div>

        <Hero title='Manage Graders' subtitle='Many hands make light work' />

        <section className='section'>
          <div className='container'>
            <h1 className='title'>Enter {idField}</h1>
            <h5 className='subtitle'>
              This instance of Zesje is configured to use {idField} for authentication.
              To allow a grader to log in using {provider}, please add their {idField}.
            </h5>
            <hr />

            <form onSubmit={this.submitName}>
              <div className='field has-addons'>
                <div className='control'>
                  <input className='input'
                    name='first_name' value={this.state.oauth_id_field}
                    onChange={this.changeIdField} type='text'
                    maxLength={100} placeholder={idField} />
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

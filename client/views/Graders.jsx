import React from 'react'

import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'

import * as api from '../api.jsx'

class Graders extends React.Component {
  state = {
    graders: [],
    name: ''
  };

  changeName = (event) => {
    this.setState({ name: event.target.value })
  }

  submitName = (event) => {
    api.post('graders', { oauth_id: this.state.name })
      .then(graders => {
        this.setState({
          name: '',
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
      })
      .catch(resp => {
        Notification.error('could not fetch graders (see Javascript console for details)')
        console.error('Error fetching graders:', resp)
      })
  }

  render () {
    return (

      <div>

        <Hero title='Manage Graders' subtitle='Many hands make light work' />

        <section className='section'>
          <div className='container'>
            <h1 className='title'>Enter the IDs</h1>
            <h5 className='subtitle'>to add them to the system</h5>
            <hr />

            <form onSubmit={this.submitName}>
              <div className='field has-addons'>
                <div className='control'>
                  <input name='first_name' value={this.state.name}
                    onChange={this.changeName} className='input' type='text'
                    maxLength={100} placeholder='Name' />
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
                  <li key={grader.id}>{grader.oauth_id}</li>
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

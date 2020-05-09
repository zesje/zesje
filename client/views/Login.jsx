import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import { Button } from 'react-bulma-components'
import 'react-bulma-components/dist/react-bulma-components.min.css'
import * as api from '../api.jsx'

class Login extends React.Component {
  state = {
    text: 'Login with Github'
  }

  componentDidMount = () => {
    this.getGraderForText() === undefined ? this.changeText('Logout') : this.changeText('Login with GitHub')
  }

  changeText = (text) => {
    this.setState({ text })
  }

  loginOrLogout = (text) => {
    if (text === undefined || text === null) {
      // login
      api.get('login')
        .then(response => {
          console.log('found response ' + response)
        })
        .catch(err => {
          console.log('found error ' + err)
        })
    } else {
      // logout
      api.get('logout')
        .then(response => {
          console.log('found response ' + response)
        })
        .catch(err => {
          console.log('found error ' + err)
        })
    }
  }

  getGraderForText = () => {
    api.get('current_grader')
      .then(response => {
        let grader = response.name
        console.log('found response ' + grader)
        return grader
      })
      .catch(err => {
        console.log('found error ' + err)
      })
  }

  render () {
    const { text } = this.state
    return (
      <div>
        <Hero title='Auth graders' subtitle='Many hands must be authenticated' />

        <section className='Login'>
          <Button onClick={() => this.loginOrLogout(text)} class='button is-info is-outlined is-medium'> { text } </Button>
        </section>

      </div>
    )
  }
}

export default Login

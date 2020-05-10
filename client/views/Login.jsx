import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import { Button } from 'react-bulma-components'
import 'react-bulma-components/dist/react-bulma-components.min.css'
import * as api from '../api.jsx'

class Login extends React.Component {
  loginOAuth = () => {
    api.get('/login_oauth').then(response => {
        window.location.href = response.redirect_oauth
    })
  }
  render () {
    return (
      <div>
        <Hero title='Login With Github' subtitle='Many hands must be authenticated' />

        <section className='Login'>
          <Button onClick={this.loginOAuth} class='button is-info is-outlined is-medium'> Login </Button>
        </section>

      </div>
    )
  }
}

export default Login

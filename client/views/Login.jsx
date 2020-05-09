import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import { Button } from 'react-bulma-components'
import 'react-bulma-components/dist/react-bulma-components.min.css'
import * as api from '../api.jsx'

class Login extends React.Component {
  // validateForm = () => {
  //   return this.state.email.length > 0 && this.state.password.length > 0
  // }
  //
  // handleSubmit = (event) => {
  //   event.preventDefault()
  // }

  requestLogin = () => {
    api.get('login')
      .catch(resp => {
        console.error('Error sending request', resp)
      })
  }

  render () {
    return (
      <div>
        <Hero title='Auth graders' subtitle='Many hands must be authenticated' />

        <section className='Login'>
          <Button class='button is-info is-outlined is-medium' onclick={() => { this.requestLogin() }}>Login with GitHub</Button>
        </section>

      </div>
    )
  }
}

export default Login

import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import { Button } from 'react-bulma-components'
import 'react-bulma-components/dist/react-bulma-components.min.css'

class Login extends React.Component {
  state = {
    password: '',
    email: '',
    setEmail: '',
    setPassword: ''
  };

  // validateForm = () => {
  //   return this.state.email.length > 0 && this.state.password.length > 0
  // }
  //
  // handleSubmit = (event) => {
  //   event.preventDefault()
  // }

  render () {
    return (
      <div>
        <Hero title='Auth graders' subtitle='Many hands must be authenticated' />

        <section className='Login'>
          <Button class='button is-info is-outlined is-medium'>Login with GitHub</Button>
        </section>

      </div>
    )
  }
}

export default Login

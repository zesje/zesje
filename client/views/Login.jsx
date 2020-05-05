import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'

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
          <button className='large-and-just-outline'>Login with GitHub</button>
        </section>

      </div>
    )
  }
}

export default Login

import React from 'react'
import {Button} from 'react-bootstrap'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import '../../node_modules/bootstrap/dist/css/bootstrap.min.css'

class Login extends React.Component {
  state = {
    password: '',
    email: '',
    setEmail: '',
    setPassword: ''
  };

  validateForm = () => {
    return this.state.email.length > 0 && this.state.password.length > 0
  }

  handleSubmit = (event) => {
    event.preventDefault()
  }

  render () {
    return (
      <div>
        <Hero title='Auth graders' subtitle='Many hands must be authenticated' />

        <div className='Login'>
          <Button variant='outline-success'>Login with GitLab</Button>{' '}
        </div>

      </div>
    )
  }
}

export default Login

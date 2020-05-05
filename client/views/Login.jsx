import React from 'react'
import { Button, FormGroup, FormControl, FormLabel } from 'react-bootstrap'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'

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
          <form onSubmit={this.handleSubmit}>

            <FormGroup controlId='email' bsSize='large'>
              <FormLabel>Email<br /> </FormLabel>
              <FormControl
                autoFocus
                type='email'
                value={this.state.email}
                onChange={e => this.setEmail(e.target.value)}
              />
            </FormGroup>

            <FormGroup controlId='password' bsSize='large'>
              <FormLabel>Password<br /> </FormLabel>
              <FormControl
                value={this.state.password}
                onChange={e => this.setPassword(e.target.value)}
                type='password'
              />
            </FormGroup>

            <Button id='buttonLogin' block bsSize='large' disabled={!this.validateForm()} type='submit'>
              Login
            </Button>

          </form>
        </div>
      </div>
    )
  }
}

export default Login

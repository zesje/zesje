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

  state = {
    text: 'Login with Github'
  }

  componentDidMount = () => {
    this.getGraderForText() === undefined ? this.changeText('Logout') : this.changeText('Login with GitHub')
  }

  changeText = (text) => {
    this.setState({ text })
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
          <Button class='button is-info is-outlined is-medium'> { text } </Button>
        </section>

      </div>
    )
  }
}

export default Login

import React from 'react'
import Hero from '../components/Hero.jsx'
import '../components/Login.css'
import { Button } from 'react-bulma-components'
import 'react-bulma-components/dist/react-bulma-components.min.css'
import * as api from '../api.jsx'

class Login extends React.Component {
    state = {
      redirect_url: '',
      provider: ''
    }
    componentDidMount = () => {
      api.get('/oauth/start').then(response => {
        if (response.is_authenticated) {
          window.location.href = window.location.origin
        }
        this.setState({redirect_url: response.redirect_oauth, provider: response.provider})
      })
    }
    loginOAuth = () => {
      window.location.href = this.state.redirect_url
    }
    render () {
      return (
        <div>
          <Hero title='Login' subtitle='Many hands must be authenticated' />

          <section className='Login'>
            <Button onClick={this.loginOAuth} class='button is-info is-outlined is-medium'> Login With {this.state.provider} </Button>
          </section>

        </div>
      )
    }
}

export default Login

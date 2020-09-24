import React from 'react'
import * as api from '../api.jsx'

class Login extends React.Component {
    state = {
      redirectURL: '',
      provider: ''
    }

    componentDidMount = () => {
      api.get('oauth/start').then(response => {
        if (!response.is_authenticated) {
          this.setState({
            redirectURL: response.redirect_oauth,
            provider: response.provider
          })
          window.sessionStorage.setItem('oauth_provider', response.provider)
          window.sessionStorage.setItem('oauth_id_field', response.oauth_id_field)
        }
      })
    }

    render () {
      return (
        <a className='button is-link' href={this.state.redirectURL}>
          <span className='icon'>
            <i className='fa fa-user' aria-hidden='true' />
          </span>
          <span>
            Login with {this.state.provider}
          </span>
        </a>
      )
    }
}

export default Login

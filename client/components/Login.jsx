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

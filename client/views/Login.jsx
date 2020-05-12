import React from 'react'
import Hero from '../components/Hero.jsx'
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
          this.props.changeURL('/')
        }
        this.setState({redirect_url: response.redirect_oauth, provider: response.provider})
      })
    }

    render () {
      return (
        <div>
          <Hero title='Login' subtitle='Many hands must be authenticated' />

          <section className='has-text-centered'>
            <a href={this.state.redirect_url}><button>Login With {this.state.provider} </button></a>
          </section>

        </div>
      )
    }
}

export default Login

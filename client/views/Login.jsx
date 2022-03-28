import React from 'react'
import { useLocation, Navigate } from 'react-router-dom'

import zesjeImage from '../components/zesje.png'

const OAuthButton = ({ provider, from }) => (
  provider != null
    ? <a className='button is-link' href={'/api/oauth/start?userurl=' + from}>
      <span className='icon'>
        <i className='fa fa-user' aria-hidden='true' />
      </span>
      <span>
        Login with {provider}
      </span>
    </a>
    : <p>Could not retrive login provider. Please, try reloading the page.</p>
)

const Login = (props) => {
  const loc = useLocation()
  const from = loc.state ? loc.state.from.pathname : '/'

  if (props.grader != null) return <Navigate to={from} replace />

  return <section className='hero is-fullheight is-vcentered is-info'>
  <div className="hero-body">
    <div className="container has-text-centered is-flex-grow-0">
    <p className="title">
      Welcome to Zesje!
    </p>
      <div className='card'>
        <div className="card-image">
          <figure className="image is-fullwidth">
            <img src={zesjeImage.src} alt="Zesje"/>
          </figure>
        </div>
        <div className="card-content">
          <OAuthButton provider={props.provider} from={from} />
        </div>
    </div>
    </div>
  </div>
  </section>
}

export default Login

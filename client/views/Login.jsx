import React from 'react'
import { useLocation, Navigate } from 'react-router-dom'

const OAuthButton = ({ provider, from }) => (
  provider != null
    ? <a className='button is-info is-inverted' href={'/api/oauth/start?userurl=' + from}>
      <span className='icon'>
        <i className='fa fa-user' aria-hidden='true' />
      </span>
      <span>
        Login with {provider}
      </span>
    </a>
    : <p>Could not retrieve login provider. Please try reloading the page.</p>
)

const Login = (props) => {
  const loc = useLocation()
  const from = loc.state ? loc.state.from.pathname : '/'

  if (props.grader != null) return <Navigate to={from} replace />

  return <section className='hero is-fullheight is-vcentered is-info'>
  <div className="hero-body">
    <div className="container has-text-centered is-flex-grow-0">
      <p className="title" style={{ fontSize: '4rem' }}>
        <i className='fa fa-edit' />
        &nbsp;Zesje
      </p>
      <OAuthButton provider={props.provider} from={from} />
    </div>
  </div>
  </section>
}

export default Login

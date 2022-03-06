import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import zesjeImage from '../components/zesje.png'

const AlreadyLoggedIn = ({ logout, grader, from }) => {
  const navigate = useNavigate()

  return <>
    <p>Already logged in as <b>{grader.name}</b></p>
    <buttons className='buttons is-centered'>
      <button className='button' onClick={logout}>Log out</button>
      <button className='button is-link' onClick={() => navigate(from, { replace: true })}>
        Continue
      </button>
    </buttons>
  </>
}

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
        {props.grader != null
          ? <AlreadyLoggedIn logout={props.logout} grader={props.grader} from={from} />
          : <OAuthButton logout={props.logout} provider={props.provider} from={from} />}
        </div>
    </div>
    </div>
  </div>
  </section>
}

export default Login

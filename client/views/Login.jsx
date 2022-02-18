
import React from 'react'

import zesjeImage from '../components/zesje.png'

const Login = (props) => (
  <section className='hero is-fullheight is-vcentered is-info'>
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
        {props.provider &&
        <div className="card-content">
          <a className='button is-link' href={'/api/oauth/start?userurl=' + window.location.pathname}>
            <span className='icon'>
              <i className='fa fa-user' aria-hidden='true' />
            </span>
            <span>
              Login with {props.provider}
            </span>
          </a>
        </div>}
    </div>
    </div>
  </div>
  </section>
)

export default Login

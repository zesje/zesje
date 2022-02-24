import React from 'react'

import Hero from '../components/Hero.jsx'

const Home = () => {
  return (
    <div>

      <Hero title='' subtitle='' />

      <section className='section'>

        <div className='container has-text-centered'>
        <span className="icon is-large has-text-info">
          <i className="fas fa-spinner fa-2x fa-pulse"></i>
        </span>
        </div>

      </section>

    </div>
  )
}

export default Home

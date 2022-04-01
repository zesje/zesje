import React from 'react'

import Hero from '../components/Hero.jsx'
import Spinner from '../components/Spinner.jsx'

const Home = () => {
  return (
    <div>

      <Hero title='' subtitle='' />

      <section className='section'>
          <Spinner />
      </section>

    </div>
  )
}

export default Home

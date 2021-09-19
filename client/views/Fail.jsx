import React from 'react'

import Hero from '../components/Hero.jsx'

const Home = (props) => {
  return (
    <div>

      <Hero
        title='Oops!'
        subtitle={props.message ? props.message : "Something went wrong :'("}
        colour='is-danger'
      />

      <section className='section'>

        <div className='container' />

      </section>

    </div>
  )
}

export default Home

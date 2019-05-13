import React from 'react'

const Hero = (props) => {
  return (
    <section className='hero is-primary is-info is-small'>
      <div className='hero-body'>
        <div className='container'>
          <h1 className='title'>
            {props.title}
          </h1>
          <h2 className='subtitle'>
            {props.subtitle}
          </h2>
        </div>
      </div>
    </section>
  )
}

export default Hero

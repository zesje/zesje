import React from 'react'

const Hero = (props) => {
  return (
    <section className={'hero is-small ' + (props.colour ? props.colour : 'is-info')}>
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

import React from 'react'

import Hero from '../components/Hero.jsx'

import homeMarkdown from './home/home.md'

const Home = () => {
  return (
    <div>

      <Hero title='Home' subtitle='Zesje - open source exam grading software' />

      <section className='section'>

        <div className='container'>
          <div className='content' dangerouslySetInnerHTML={{__html: homeMarkdown}} />
        </div>

      </section>

    </div>
  )
}

export default Home

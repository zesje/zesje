import React from 'react'

import homeMarkdown from './home/home.md'

const Home = () => {
  return (
    <div>

      <section className='section'>

        <div className='container'>
          <div className='content' dangerouslySetInnerHTML={{__html: homeMarkdown}} />
        </div>

      </section>

    </div>
  )
}

export default Home

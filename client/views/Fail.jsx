import React from 'react'

const Home = (props) => {
  return (
    <div>

      <section className='section'>

        <div className='container'>
          <h1 className='title'>Oops</h1>
          <h5 className='subtitle'>{props.message ? props.message : "Something went wrong :'("}</h5>
        </div>

      </section>

    </div>
  )
}

export default Home

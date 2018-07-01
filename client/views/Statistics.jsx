import React from 'react'

import Hero from '../components/Hero.jsx'

class Statistics extends React.Component {
  render () {
    return (
      <div>

        <Hero title='Statistics' subtitle='Analyse how to the exam was made' />

        <section className='section'>

          <div className='container'>

            <figure className='image is-4by3'>
              <img src={'api/images/summary/' + this.props.exam.id} />
            </figure>

          </div>

        </section>

      </div >
    )
  }
}

export default Statistics

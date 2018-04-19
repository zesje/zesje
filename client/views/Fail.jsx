import React from 'react';

import Hero from '../components/Hero.jsx';

const Home = (props) => {
  return (
      <div>

        <Hero title='Oops!' subtitle={props.message ? props.message : "Something went wrong :'("} />

        <section className="section">

          <div className="container">
           
          </div>

        </section>
        
      </div>
  )
}

export default Home;
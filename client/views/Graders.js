import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import GraderManager from '../components/GradersManager';

const Graders = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Manage Graders' subtitle='Many hands make light work' />
        
        <section className="section">
          <div className="container">
            <h1 className='title'>Enter the names</h1>
            <h5 className='subtitle'>to add them to the system</h5>
            <hr />
            
            <GraderManager />
          </div>
        </section>

        <Footer />

      </div>
  )
}

export default Graders;

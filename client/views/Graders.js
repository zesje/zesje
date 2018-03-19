import React from 'react';

import Hero from '../components/Hero';
import GraderManager from '../components/GradersManager';

const Graders = () => {
  return (
      <div>

        <Hero title='Manage Graders' subtitle='Many hands make light work' />
        
        <section className="section">
          <div className="container">
            <h1 className='title'>Enter the names</h1>
            <h5 className='subtitle'>to add them to the system</h5>
            <hr />
            
            <GraderManager />
          </div>
        </section>

      </div>
  )
}

export default Graders;

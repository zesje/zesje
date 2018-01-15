import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Reset = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Reset' subtitle="Please don't hurt my database :(" />
        
        <section className="section">


          <div className="container">
            <h1 className='title'>Are your very sure?</h1>
            <h5 className='subtitle'>This cannot be undone...</h5>
            
            <hr />

            <div class="field is-grouped">
              <div class="control">
                <button class="button is-danger">Everything</button>
              </div>
              <div class="control">
                <button class="button is-warning">People</button>
              </div>
              <div class="control">
                <button class="button is-warning">Exam</button>
              </div>
              <div class="control">
                <button class="button is-warning">Student validation</button>
              </div>
              <div class="control">
                <button class="button is-warning">Gradeing</button>
              </div>
            </div>
          </div>


        </section>

      </div>
  )
}

export default Reset;
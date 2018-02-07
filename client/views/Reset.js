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

            <nav className="level">

                <div class="level-item control">
                  <button class="button is-danger">Everything</button>
                </div>
                <div class="level-item control">
                  <button class="button is-warning">Exams</button>
                </div>
                <div class="level-item control">
                  <button class="button is-warning">Students</button>
                </div>
                <div class="level-item control">
                  <button class="button is-warning">Grading</button>
                </div>
                <div class="level-item control">
                  <button class="button is-warning">Graders</button>
                </div>
            </nav>
          </div>


        </section>

      </div>
  )
}

export default Reset;
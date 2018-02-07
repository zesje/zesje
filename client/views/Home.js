import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Home = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Home' subtitle='Zesje - open source exam grading software' />

        <section className="section">


          <div className="container">
            <h1 className='title'>About this software</h1>
            <h5 className='subtitle'>Here can be a information text, but I am not gonna write that ATM..</h5>
            
            <hr />

            Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat
            Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
          </div>


        </section>
        
        <Footer />
        
      </div>
  )
}

export default Home;

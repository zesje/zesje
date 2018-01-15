import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Reset = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Reset' subtitle="Please don't hurt my database :(" />
        
        <h1>React Router demo</h1>
        Hoi dit de Reset
        <Footer />
        
      </div>
  )
}

export default Reset;
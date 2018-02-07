import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Grade = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Grade' subtitle='This is where the magic happens!' />
        
        <h1>React Router demo</h1>
        Hoi dit de Grade

        <Footer />

      </div>
  )
}

export default Grade;
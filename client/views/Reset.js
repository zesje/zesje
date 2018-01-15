import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';

const Reset = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Reset' subtitle="Please don't hurt my database :(" />
        
        <h1>React Router demo</h1>
        Hoi dit de Reset
      </div>
  )
}

export default Reset;
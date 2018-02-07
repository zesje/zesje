import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const CheckStudents = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Check Students' subtitle='Sanity check for the students' />

        <h1>React Router demo</h1>
        Hoi dit de CheckStudents
        <Footer />

       </div>
  )
}

export default CheckStudents;
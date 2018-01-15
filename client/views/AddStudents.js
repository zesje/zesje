import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const AddStudents = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Add Students' subtitle='Tell me who made this exam' />

        <h1>React Router demo</h1>
        Hoi dit de AddStudents

        <Footer />
      
      </div>
  )
}

export default AddStudents;
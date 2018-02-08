import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const StatisticsDashboard = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Statistics Dashboard' subtitle='Is your exam sane?' />

        <h1>React Router demo</h1>
        Hoi dit de Statistics Dashboard
        <Footer />

       </div>
  )
}

export default StatisticsDashboard;

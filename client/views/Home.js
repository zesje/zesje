import React from 'react';
import NavBar from '../components/NavBar';

const Home = () => {
  return (
      <div>

        <NavBar />

        <section className="hero is-primary">
          <div className="hero-body">
            <p className="title">
              Documentation
            </p>
            <p className="subtitle">
              Everything you need to <strong>create a website</strong> with Bulma
            </p>
          </div>
        </section>
        
        <h1>React Router demo</h1>
        Hoi dit de homepagina
      </div>
  )
}

export default Home;

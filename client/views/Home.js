import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import ReactMarkdown from 'react-markdown';

import homeMarkdown from './home.md'

const Home = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Home' subtitle='Zesje - open source exam grading software' />

        <section className="section">

          <div className="container">
            <div className="content">
                <ReactMarkdown source={homeMarkdown} />
            </div>
          </div>

        </section>
        
        <Footer />
        
      </div>
  )
}

export default Home;

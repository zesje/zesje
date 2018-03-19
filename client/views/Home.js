import React from 'react';
import ReactMarkdown from 'react-markdown';

import Hero from '../components/Hero';

import homeMarkdown from './home.md'

const Home = () => {
  return (
      <div>

        <Hero title='Home' subtitle='Zesje - open source exam grading software' />

        <section className="section">

          <div className="container">
            <div className="content">
                <ReactMarkdown source={homeMarkdown} />
            </div>
          </div>

        </section>
        
      </div>
  )
}

export default Home;

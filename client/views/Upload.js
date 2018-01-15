import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Upload = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Upload' subtitle='Omnomnomnom Exams!' />

        <section className="section">


          <div className="container">
            <h1 className='title'>Select your PDF file</h1>
            <h5 className='subtitle'>And we will take care of the rest</h5>
            
            <hr />

            <div className="file">
              <label className="file-label">

                <input className="file-input" type="file" name="resume" />
                <span className="file-cta">
                  <span className="file-icon">
                    <i className="fa fa-upload"></i>
                  </span>
                  <span className="file-label">
                    Choose a file…
                  </span>
                </span>

              </label>
            </div>


          </div>

        </section>

        <Footer />

      </div>
  )
}

export default Upload;
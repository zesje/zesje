import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const Upload = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Exams' subtitle="Omnomnomnom PDF's!" />

        <section className="section">


          <div className="container">

            <nav className="level">
              <div className="level-item has-text-centered">
                <div>
                  <p><h3 className='title'>Select an exam</h3></p>
                  <h5 className='subtitle'>and we will work some PDF magic!</h5>
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
                      <span className="file-name">
                        scanned_exams.pdf
                      </span>
                    </label>
                  </div>
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
                      <span className="file-name">
                        exam_metadata.csv
                      </span>
                    </label>
                  </div>
                </div>
              </div>
              <div className="level-item has-text-centered">
                <div>
                  <p><h3 className='title'>And the student list</h3></p>
                  <h5 className='subtitle'>Don't worry if it isn't complete</h5>
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
                      <span className="file-name">
                        enrolled_students.csv
                      </span>
                    </label>
                  </div>
                </div>
              </div>
            </nav>

          </div>

        </section>

        <Footer />

      </div>
  )
}

export default Upload;
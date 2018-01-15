import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';


var shortButton = {width: '336px'};

const Upload = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Exams' subtitle="Omnomnomnom PDF's!" />

        <section className="section">


          <div className="container">
            <div className="columns">
              <div className="column">
                <h3 className='title'>Upload new exam</h3>
                <h5 className='subtitle'>and we will work some PDF magic!</h5>

                <input class="input" type="text" style={shortButton} placeholder="Name" />

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
                <br />
                <button className='button is-info'>Upload</button>
              </div>
              <div className="column">
                <h3 className='title'>Or edit an existing</h3>
                <h5 className='subtitle'>to make some minor adjustments or start over</h5>

                <div class="select">
                  <select>
                    <option>Midterm 5-12</option>
                    <option>Final 30-1</option>
                  </select>
                </div>
                <textarea class="textarea" placeholder="Config will appearr here..."></textarea>
                <button className='button is-success'>Save</button>
                <button className='button is-danger'>Delete</button>


              </div>
            </div>

          </div>
        </section>

        <Footer />

      </div>
  )
}

export default Upload;
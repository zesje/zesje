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
                <h3 className='title'>Upload new exam config</h3>
                <h5 className='subtitle'>then we know that to do with PDF's</h5>

                <div className="file has-name is-boxed">
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
                      exams_configs.yaml
                    </span>
                  </label>
                </div>
                <br />
                <button className='button is-info'>Upload</button>
              </div>

              <div className="column">
                <h3 className='title'>And tweak the config</h3>
                <h5 className='subtitle'>Fix misalignments</h5>
                <div className="select">
                  <select>
                    <option>Midterm 5-12</option>
                    <option>Final 30-1</option>
                  </select>
                </div>
                <textarea className="textarea" placeholder="YAML config will appear here..."></textarea>
                <button className='button is-success'>Save</button>
              </div>


              <div className="column">
                <h3 className='title'>And upload PDF's</h3>
                <h5 className='subtitle'>we will work some magic!</h5>

                <div className="file has-name is-boxed">
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
                      Exams.pdf
                    </span>
                  </label>
                </div>

                <br />

                <aside className="menu">
                <p className="menu-label">
                  Previously uploaded
                </p>
                  <ul className="menu-list">
                    <li>midterm.pdf</li>
                    <li>final_exam.pdf</li>
                  </ul>
                </aside>


              </div>
            </div>

          </div>
        </section>

        <Footer />

      </div>
  )
}

export default Upload;
import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import Dropzone from 'react-dropzone'


class Exams extends React.Component {

  onDrop(files) {
    console.log(files);
  }


  render () {
    return <div>

      <NavBar />
        
      <Hero title='Exams' subtitle="Omnomnomnom PDF's!" />

      <section className="section">

        <div className="container">
          <div className="columns">
            <div className="column has-text-centered">
              <h3 className='title'>Upload new exam config</h3>
              <h5 className='subtitle'>then we know that to do with PDF's</h5>

              <Dropzone style={{}} activeStyle={{borderStyle: 'dashed', width: 'fit-content', margin: 'auto'}} onDrop={this.onDrop.bind(this)}>
                <div className="file has-name is-boxed is-centered">
                  <label className="file-label"> 
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
              </Dropzone>

              
            </div>

            <div className="column has-text-centered">
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


            <div className="column has-text-centered">
              <h3 className='title'>And upload PDF's</h3>
              <h5 className='subtitle'>we will work some magic!</h5>

              <Dropzone style={{}} activeStyle={{borderStyle: 'dashed', width: 'fit-content', margin: 'auto'}} onDrop={this.onDrop.bind(this)}>
                <div className="file has-name is-boxed is-centered">
                  <label className="file-label">
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
              </Dropzone>


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
  }
}

export default Exams;
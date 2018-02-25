import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import test_image from '../student.jpg';

  const CheckStudents = () => {

    var inputStyle = {
      width:'6em'
    };

  return (
    <div>

      <NavBar />

      <Hero title='Match Students' subtitle='Who made what?' />

      <section className="section">

        <div className="container">

          <div className="columns">
            <div className="column is-one-quarter-desktop is-one-third-tablet">

              <div className="is-hidden-desktop">
                <div className="control has-icons-left">
                  <div className="select is-info is-fullwidth">
                    <select>
                      <option>Select exams</option>
                      <option>Not me! plEASE :(</option>
                    </select>
                  </div>
                  <span className="icon is-small is-left">
                    <i className="fa fa-pencil"></i>
                  </span>
                </div>
              </div>

              <nav className="panel">
                <p className="panel-heading">
                  Students
                </p>
                <p className="panel-tabs">
                  <a className="is-active">Unassigned</a>
                  <a>all</a>
                </p>
                <div className="panel-block">
                  <p className="control has-icons-left">
                    <input className="input" type="text" placeholder="Search" />
                    <span className="icon is-left">
                      <i className="fa fa-search"></i>
                    </span>
                  </p>
                </div>
                <a className="panel-block is-active">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Thomas Roos
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Henk de boer
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Jan de Vries
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Jaap Smit
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Nana Batman
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  John Doe
                </a>
                <a className="panel-block">
                  <span className="panel-icon">
                    <i className="fa fa-user"></i>
                  </span>
                  Lala loepsie
                </a>
                <label className="panel-block">
                  <input type="checkbox" />
                  Random tick
                </label>
                <div className="panel-block is-hidden-mobile">
                  <button className="button is-link is-outlined is-fullwidth">
                    Batch upload
                  </button>
                </div>
              </nav>
            </div>

            <div className="column">
              
                <div className="level">

                  <div className="level-left is-hidden-touch">
                    <div className="level-item">
                      <div className="control has-icons-left">
                        <div className="select is-info is-fullwidth">
                          <select>
                            <option>Select exams</option>
                            <option>Not me! plEASEeeeeee :(</option>
                          </select>
                        </div>
                        <span className="icon is-small is-left">
                          <i className="fa fa-pencil"></i>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="level-right">
                    <div className="level-item">
                      <div className="field has-addons is-mobile">
                        <div className="control">
                          <button type="submit" className="button is-info is-rounded is-hidden-mobile">unchecked</button>
                          <button type="submit" className="button">Previous</button>
                        </div>
                          <div className="control">
                            <input className="input is-rounded has-text-centered" type="number"
                              min="0" step="1" value="1465" maxLength="4" size="6" style={inputStyle} />
                          </div>
                        <div className="control">
                          <button type="submit" className="button">Next</button>
                          <button type="submit" className="button is-info is-rounded is-hidden-mobile">unchecked</button>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

                <div className="level is-mobile">
                  <div className="level-item is-hidden-mobile">
                    <progress className="progress is-success" value="64" max="100">64%</progress>
                  </div>
                  <div className="level-right">
                    <div className="level-item has-text-grey">
                     <i>1465 / 2289</i>
                    </div>
                    <div className="level-item has-text-success">
                     <b>64%</b>
                    </div>
                  </div>
                </div>

                <p className="box">
                  <img src={test_image} />
                </p>

            </div>
      
            </div>
          </div>


      </section>


      <Footer />

    </div>
  )
}

export default CheckStudents;
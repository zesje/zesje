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

              <div class="is-hidden-desktop">
                <div class="control has-icons-left">
                  <div class="select is-info is-fullwidth">
                    <select>
                      <option>Select exams</option>
                      <option>Not me! plEASE :(</option>
                    </select>
                  </div>
                  <span class="icon is-small is-left">
                    <i class="fa fa-pencil"></i>
                  </span>
                </div>
              </div>

              <nav class="panel">
                <p class="panel-heading">
                  Students
                </p>
                <p class="panel-tabs">
                  <a class="is-active">Unassigned</a>
                  <a>all</a>
                </p>
                <div class="panel-block">
                  <p class="control has-icons-left">
                    <input class="input" type="text" placeholder="Search" />
                    <span class="icon is-left">
                      <i class="fa fa-search"></i>
                    </span>
                  </p>
                </div>
                <a class="panel-block is-active">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Thomas Roos
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Henk de boer
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Jan de Vries
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Jaap Smit
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Nana Batman
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  John Doe
                </a>
                <a class="panel-block">
                  <span class="panel-icon">
                    <i class="fa fa-user"></i>
                  </span>
                  Lala loepsie
                </a>
                <label class="panel-block">
                  <input type="checkbox" />
                  Random tick
                </label>
                <div class="panel-block is-hidden-mobile">
                  <button class="button is-link is-outlined is-fullwidth">
                    Batch upload
                  </button>
                </div>
              </nav>
            </div>

            <div className="column">
              
                <div class="level">

                  <div class="level-left is-hidden-touch">
                    <div class="level-item">
                      <div class="control has-icons-left">
                        <div class="select is-info is-fullwidth">
                          <select>
                            <option>Select exams</option>
                            <option>Not me! plEASEeeeeee :(</option>
                          </select>
                        </div>
                        <span class="icon is-small is-left">
                          <i class="fa fa-pencil"></i>
                        </span>
                      </div>
                    </div>
                  </div>

                  <div class="level-right">
                    <div class="level-item">
                      <div class="field has-addons is-mobile">
                        <div class="control">
                          <button type="submit" class="button is-info is-rounded is-hidden-mobile">unchecked</button>
                          <button type="submit" class="button">Previous</button>
                        </div>
                          <div class="control">
                            <input class="input is-rounded has-text-centered" type="number"
                              min="0" step="1" value="1465" maxLength="4" size="6" style={inputStyle} />
                          </div>
                        <div class="control">
                          <button type="submit" class="button">Next</button>
                          <button type="submit" class="button is-info is-rounded is-hidden-mobile">unchecked</button>
                        </div>
                      </div>
                    </div>
                  </div>

                </div>

                <div class="level is-mobile">
                  <div class="level-item is-hidden-mobile">
                    <progress class="progress is-success" value="64" max="100">64%</progress>
                  </div>
                  <div class="level-right">
                    <div class="level-item has-text-grey">
                     <i>1465 / 2289</i>
                    </div>
                    <div class="level-item has-text-success">
                     <b>64%</b>
                    </div>
                  </div>
                </div>

                <p class="box">
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
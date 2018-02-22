import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import test_image from '../student.jpg';

const CheckStudents = () => {
  return (
      <div>

        <NavBar />
        
        <Hero title='Match Students' subtitle='Who made what?' />

        <section className="section">
          
        <div className="container">


          <div className="columns">
            <div className="column is-one-quarter">
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
            <div className="column">
              <progress class="progress is-success is-large" value="64" max="100">64%</progress>
            </div>
          </div>


        <div class="columns">

          <div class="column is-one-quarter">        
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
                <label class="panel-block">
                  <input type="checkbox" />
                  Random tick
                </label>
                <div class="panel-block">
                  <button class="button is-link is-outlined is-fullwidth">
                    Batch upload
                  </button>
                </div>
              </nav>
          </div>


          <div class="column">
            
            <div class="columns">
              <div class="column">
                <div class="buttons is-right">
                  <a class="button is-info is-rounded">Previous</a>
                </div>
              </div>
              <div class="column is-2">
                <input class="input is-rounded has-text-centered" type="number"
                   min="0" step="1" placeholder="Submission ID" value="1465"/>
              </div>
              <div class="column">
                <div class="buttons is-left">
                  <a class="button is-info is-rounded">Next</a>
                </div>
              </div>
            </div>

            <p class="box">
              <img src={test_image} />
            </p>


          </div>

        </div>

        {/*
          <div className="container">
          <div className="columns">
            <div className="column is-one-fifth">
              <p className="bd-notification is-warning">students search and select</p>
            </div>
            <div className="column">exams stuff</div>
          </div>
        </div>
        */}

        </div>

        </section>

        
        <Footer />

       </div>
  )
}

export default CheckStudents;
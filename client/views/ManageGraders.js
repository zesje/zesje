import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

const AddGraders = () => {
  return (
      <div>

        <NavBar />

        <Hero title='Add Graders' subtitle='Many hands make light work' />
        
        <section className="section">


          <div className="container">
            <h1 className='title'>Enter the names</h1>
            <h5 className='subtitle'>to add them to the system</h5>
            
            <hr />

              
            <div class="field has-addons">
              <div class="select">
                <select>
                  <option>Henk de Vries</option>
                  <option>Jan Janssen</option>
                </select>
              </div>
              <div class="control">
                <a class="button is-danger">Delete</a>
              </div>
            </div>

            <div class="field has-addons">
              <div class="control">
                <input class="input" type="text" placeholder="Add someone" />
              </div>
              <div class="control">
                <a class="button is-info">
                  Add
                </a>
              </div>
            </div>


            


          </div>

        </section>

        <Footer />

      </div>
  )
}

export default AddGraders;

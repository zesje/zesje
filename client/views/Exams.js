import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import Dropzone from 'react-dropzone'

import * as api from '../api'


class Exams extends React.Component {

  constructor(props) {
    super(props);
    this.state = {configSelected: [''],
                  uploadedPDFs: ['']};

    this.onDropYAML = this.onDropYAML.bind(this);
    this.onDropPDF = this.onDropPDF.bind(this);
  }

  onDropYAML(accepted, rejected) {
    if (rejected.length > 0) {
      alert('Please upload a YAML..')
    } else {
      console.log(accepted);
      this.setState({configSelected: [accepted[0].name]})

      var data = new FormData()
      data.append('file', accepted[0])

      api.post('exams', data)
      .then(() =>
        alert('Thank you for your upload, it was delicious')
        // TODO: update interface to reflect uploaded YAML
        //       I reckon we will need a different format for this.state
      )
      .catch(resp => {
        alert('failed to upload yaml (see javascript console for details)')
        console.error('failed to upload YAML:', resp)
      })
    }
  }
  
  onDropPDF(accepted, rejected) {
    if (rejected.length > 0) {
      alert('Please upload a PDF..')
    } else {
      // TODO: implement PDF upload
      console.log(accepted);
      this.setState({uploadedPDFs: [accepted[0].name]})
    }
  }


  render () {

    var isDisabled = this.state.configSelected[0].length == 0;
    var textStyle = {
      color: isDisabled ? 'grey' : 'black'
    };

    return <div>

      <NavBar />
        
      <Hero title='Exams' subtitle="Omnomnomnom PDF's!" />

      <section className="section">

        <div className="container">
          <div className="columns">
            <div className="column has-text-centered">
              <h3 className='title'>Upload new exam config</h3>
              <h5 className='subtitle'>then we know that to do with PDF's</h5>

              <Dropzone accept=".yml, text/yaml, text/x-yaml, application/yaml, application/x-yaml"
                style={{}} activeStyle={{borderStyle: 'dashed', width: 'fit-content', margin: 'auto'}} onDrop={this.onDropYAML}>
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
                    <span className="file-name has-text-centered">
                      <i>midterm_config</i>.yml
                    </span>
                  </label>
                </div>
              </Dropzone>

              
            </div>

            <div className="column has-text-centered" style={textStyle}>
              <h3 className='title' style={textStyle}>And tweak the config</h3>
              <h5 className='subtitle' style={textStyle}>Fix misalignments</h5>
              <div className="select">
                <select disabled={isDisabled}>
                  {this.state.configSelected.map((config) => {
                      return <option key={config}>{config}</option>
                  })}
                </select>
              </div>
              <textarea className="textarea" placeholder="YAML config will appear here..." disabled={isDisabled}></textarea>
              <button className='button is-success' disabled={isDisabled}>Save</button>
            </div>


            <div className="column has-text-centered">
              <h3 className='title' style={textStyle}>And upload PDF's</h3>
              <h5 className='subtitle' style={textStyle}>we will work some magic!</h5>

              <Dropzone accept={"application/pdf"} style={{}}
                activeStyle={{borderStyle: 'dashed', width: 'fit-content', margin: 'auto'}} onDrop={this.onDropPDF.bind(this)} disabled={isDisabled}>
                <div className="file has-name is-boxed is-centered">
                  <label className="file-label">
                    <span className="file-cta" disabled={isDisabled}>
                      <span className="file-icon">
                        <i className="fa fa-upload"></i>
                      </span>
                      <span className="file-label">
                        Choose a file…
                      </span>
                    </span>
                    <span className="file-name has-text-centered" disabled={isDisabled}>
                      <i>scanned_exam</i>.PDF
                    </span>
                  </label>
                </div>
              </Dropzone>


              <br />

              <aside className="menu" style={textStyle}>
              <p className="menu-label">
                Previously uploaded
              </p>
                <ul className="menu-list">
                {this.state.uploadedPDFs.map((PDF) => {
                      return <li key={PDF}>{PDF}</li>
                  })}
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

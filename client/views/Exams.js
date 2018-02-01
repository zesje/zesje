import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import Dropzone from 'react-dropzone'

import * as api from '../api'


class Exams extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
        exams: [],
        selected_exam: {
            id: "",
            name: "",
            yaml: "",
        },
    };
    this.onDropYAML = this.onDropYAML.bind(this);
    this.onDropPDF = this.onDropPDF.bind(this);
    this.putYaml = this.putYaml.bind(this);
    this.updateYaml = this.updateYaml.bind(this);
    this.selectExam = this.selectExam.bind(this);

  }

  onDropYAML(accepted, rejected) {
    if (rejected.length > 0) {
      alert('Please upload a YAML..')
      return
    }
    var data = new FormData()
    data.append('yaml', accepted[0])
    api.post('exams', data)
    .then(new_exam => {
      // if reall is new exam then add to list of exams
      if (!this.state.exams.some(exam => new_exam.id == exam.id)) {
          this.setState(prev => ({
            exams: [...prev.exams, new_exam],
          }))
      }
      this.setState({
          selected_exam: new_exam,
      })
      alert('Thank you for your upload, it was delicious')
    })
    .catch(resp => {
      alert('failed to upload yaml (see javascript console for details)')
      console.error('failed to upload YAML:', resp)
    })
  }

  putYaml() {
    const exam_id = this.state.selected_exam.id
    api.put('exams/' + exam_id, {yaml: this.state.selected_exam.yaml})
    .then(() => alert('thank you for the update; it was delicious'))
    .catch(resp => {
        alert('failed to update the YAML (see javascript console)')
        console.error('failed to update YAML', resp)
    })
  }

  updateYaml(event) {
    const yaml = event.target.value
    this.setState(prev => {
        return {
          selected_exam: {
            id: prev.selected_exam.id,
            name: prev.selected_exam.name,
            yaml: yaml,
          }
        }
    })
  }

  selectExam(event) {
    const new_exam_id = event.target.value
    api.get('exams/' + new_exam_id)
    .then(exam =>
        this.setState(prev => {
            return {selected_exam: exam}
        })
    )
  }

  
  onDropPDF(accepted, rejected) {
    if (rejected.length > 0) {
      alert('Please upload a PDF..')
    } else {
      // TODO: implement PDF upload
      console.log('would upload PDF here')
    }
  }

  componentDidMount() {
    api.get('exams')
    .then(exams => {
        this.setState({exams: exams})
        if (exams.length > 0) {
            var first_exam = exams[0].id
            api.get('exams/' + first_exam)
            .then(exam => this.setState({selected_exam: exam}))
        }
    })
    .catch(err => {
        alert('failed to get exams (see javascript console for details)')
        console.error('failed to get exams:', err)
        throw err
    })
  }

  render () {

    var isDisabled = this.state.exams.length == 0;
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
                <select disabled={isDisabled}
                        value={this.state.selected_exam.id}
                        onChange={this.selectExam}>
                  {this.state.exams.map((exam) => {
                      return <option value={exam.id}>{exam.name}</option>
                  })}
                </select>
              </div>
              <textarea className="textarea" placeholder="YAML config will appear here..." disabled={isDisabled}
                        value={this.state.selected_exam.yaml} onChange={this.updateYaml}>
              </textarea>
              <button className='button is-success' disabled={isDisabled}
                      onClick={this.putYaml}>
              Save
              </button>
            </div>


            <div className="column has-text-centered">
              <h3 className='title' style={textStyle}>And upload PDF's</h3>
              <h5 className='subtitle' style={textStyle}>we will work some magic!</h5>

              <Dropzone accept={"application/pdf"} style={{}}
                activeStyle={{borderStyle: 'dashed', width: 'fit-content', margin: 'auto'}}
                onDrop={this.onDropPDF.bind(this)}
                disabled={isDisabled}>
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

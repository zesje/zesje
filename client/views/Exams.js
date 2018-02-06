import React from 'react';
import NavBar from '../components/NavBar';
import Hero from '../components/Hero';
import Footer from '../components/Footer';

import Dropzone from 'react-dropzone'
import Spinner from 'react-spinkit'

import * as api from '../api'


class Exams extends React.Component {

  constructor(props) {
    super(props);
    this.state = {
        exams: [],
        selected_exam: {
            id: null,
            name: null,
            yaml: null,
            pdfs: [],
        },
    };

    this.onDropYAML = this.onDropYAML.bind(this);
    this.onDropPDF = this.onDropPDF.bind(this);
    this.putYaml = this.putYaml.bind(this);
    this.updateYaml = this.updateYaml.bind(this);
    this.selectExam = this.selectExam.bind(this);
    this.pdfStatus= this.pdfStatus.bind(this);
    this.updatePDFList= this.updatePDFList.bind(this);

    this._pdfUpdater = null;
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
      this.selectExam(new_exam.id)
      alert('Thank you for your upload, it was delicious')
    })
    .catch(resp => {
      alert('failed to upload yaml (see javascript console for details)')
      console.error('failed to upload YAML:', resp)
    })
  }

  putYaml() {
    const exam_id = this.state.selected_exam.id
    api.patch('exams/' + exam_id, {yaml: this.state.selected_exam.yaml})
    .then(() => alert('thank you for the update; it was delicious'))
    .catch(resp => {
        alert('failed to update the YAML (see javascript console)')
        console.error('failed to update YAML', resp)
    })
  }

  updateYaml(event) {
    const yaml = event.target.value
    this.setState(prev => ({
        selected_exam: Object.assign(prev.selected_exam, {yaml: yaml})
    }))
  }

  selectExam(exam_id) {
    api.get('exams/' + exam_id)
    .then(exam =>
        this.setState(prev => ({
            selected_exam: Object.assign(prev.selected_exam, exam)
        }))
    )

    api.get('pdfs/' + exam_id)
    .then(pdfs =>
        this.setState(prev => ({
            selected_exam: Object.assign(prev.selected_exam, {pdfs: pdfs})
        }))
    )
  }

  updatePDFList() {
    if( this.state.selected_exam.id == null ) {
        return
    }
    api.get('pdfs/' + this.state.selected_exam.id)
    .then(pdfs =>
        this.setState(prev => ({
            selected_exam: Object.assign(prev.selected_exam, {pdfs: pdfs})
        }))
    )
  }

  pdfStatus(pdf) {
    switch(pdf.status) {
      case "processing":
        const style = {display: "inline-block", top: "6px"}
        return <div>{pdf.name} <Spinner name="circle" style={style} fadeIn='none'/> <i>{pdf.message}</i></div>
      case "success":
        return <div>{pdf.name} <i className="fa fa-check"></i>{pdf.message}</div>
      case "error":
        return <div>{pdf.name} <i className="fa fa-times"></i><i>{pdf.message}</i></div>
    }
  }

  onDropPDF(accepted, rejected) {
    if (rejected.length > 0) {
      alert('Please upload a PDF..')
      return
    }
    var data = new FormData()
    data.append('pdf', accepted[0])
    api.post('pdfs/' + this.state.selected_exam.id, data)
    .then(() => {
       api.get('pdfs/' + this.state.selected_exam.id)
      .then(pdfs =>
          this.setState(prev => ({
              selected_exam: Object.assign(prev.selected_exam, {pdfs: pdfs})
          }))
      )
      alert('Thank you for your upload, it was delicious')
    })
    .catch(resp => {
      alert('failed to upload pdf (see javascript console for details)')
      console.error('failed to upload PDF:', resp)
    })
  }

  componentDidMount() {
    api.get('exams')
    .then(exams => {
        this.setState({exams: exams})
        if (exams.length > 0) {
            var first_exam = exams[0].id
            this.selectExam(first_exam)
        }
    })
    .catch(err => {
        alert('failed to get exams (see javascript console for details)')
        console.error('failed to get exams:', err)
        throw err
    })

    this._pdfUpdater = setInterval(this.updatePDFList, 1000)
  }

  componentWillUnmount() {
      if( this._pdfUpdater ) {
          clearInterval(this._pdfUpdater)
          this._pdfUpdater = null
      }
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
                        onChange={ev => this.selectExam(ev.target.value)}>
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
                {this.state.selected_exam.pdfs.map(pdf =>
                    <li>{this.pdfStatus(pdf)}</li>
                )}
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

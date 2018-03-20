import React from 'react';
import Dropzone from 'react-dropzone'

import Hero from '../components/Hero.jsx';

import * as api from '../api.jsx'

const StatusPDF = props => {
  let iconClass = "fa fa-";
  switch (props.pdf.status) {
    case "processing":
      iconClass += "refresh fa-spin";
      break;
    case "success":
      iconClass += "check";
      break;
    case "error":
      iconClass += "times";
      break;
  }
  return <div>
    {props.pdf.name}&emsp;<i className={iconClass} />
    <i>&nbsp;{props.pdf.message}</i>
  </div>
}

const DropzoneContent = props => (
  <div className="file has-name is-boxed is-centered">
    <label className="file-label">
      <span className="file-cta" disabled={props.disabled}>
        <span className="file-icon">
          <i className="fa fa-upload"></i>
        </span>
        <span className="file-label">
          Choose a file…
        </span>
      </span>
    </label>
  </div>
)

class Exams extends React.Component {
  state = {
    exams: [],
    selected_exam: {
      id: undefined,
      name: undefined,
      yaml: undefined,
      pdfs: [],
    },
  };


  onDropYAML = (accepted, rejected) => {
    if (rejected.length > 0) {
      alert('Please upload a YAML..')
      return
    }
    const data = new FormData()
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

  putYaml = () => {
    const exam_id = this.state.selected_exam.id
    api.patch('exams/' + exam_id, { yaml: this.state.selected_exam.yaml })
      .then(() => alert('thank you for the update; it was delicious'))
      .catch(resp => {
        alert('failed to update the YAML (see javascript console)')
        console.error('failed to update YAML', resp)
      })
  }

  updateYaml = (event) => {
    this.setState({
      selected_exam: {
        ...this.state.selected_exam,
        yaml: event.target.value
      }
    })
  }

  selectExam = (exam_id) => {
    api.get('exams/' + exam_id)
      .then(exam => {
        api.get('pdfs/' + exam_id)
          .then(pdfs => {
            exam.pdfs = pdfs;
            this.setState({
              selected_exam: exam
            })
          })
      })
  }

  updatePDFList = () => {
    if (this.state.selected_exam.id == null) {
      return
    }
    api.get('pdfs/' + this.state.selected_exam.id)
      .then(pdfs =>
        this.setState({
          selected_exam: {
            ...this.state.selected_exam,
            pdfs: pdfs
          }
        })
      )
  }

  onDropPDF = (accepted, rejected) => {
    if (rejected.length > 0) {
      alert('Please upload a PDF..')
      return
    }
    accepted.map(file => {
      const data = new FormData()
      data.append('pdf', file)
      api.post('pdfs/' + this.state.selected_exam.id, data)
        .then(() => {
          api.get('pdfs/' + this.state.selected_exam.id)
            .then(pdfs =>
              this.setState({
                selected_exam: {
                  ...this.state.selected_exam,
                  pdfs: pdfs
                }
              })
            )
        })
        .catch(resp => {
          alert('failed to upload pdf (see javascript console for details)')
          console.error('failed to upload PDF:', resp)
        })
    })
  }

  componentDidMount() {
    api.get('exams')
      .then(exams => {
        this.setState({ exams: exams })
        if (exams.length > 0) {
          this.selectExam(exams[0].id)
        }
      })
      .catch(err => {
        alert('failed to get exams (see javascript console for details)')
        console.error('failed to get exams:', err)
        throw err
      })

    this.pdfUpdater = setInterval(this.updatePDFList, 1000)
  }

  componentWillUnmount() {
    clearInterval(this.pdfUpdater);
  }

  render() {

    const isDisabled = this.state.exams.length == 0;
    const textStyle = {
      color: isDisabled ? 'grey' : 'black'
    };

    return <div>

      <Hero title='Exams' subtitle="Omnomnomnom PDF's!" />

      <section className="section">

        <div className="container">
          <div className="columns">
            <div className="column has-text-centered">
              <h3 className='title'>Upload new exam config</h3>
              <h5 className='subtitle'>then we know that to do with PDF's</h5>

              <Dropzone accept=".yml, text/yaml, text/x-yaml, application/yaml, application/x-yaml"
                style={{}} activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                onDrop={this.onDropYAML}
                disablePreview
                multiple={false}
              >
                <DropzoneContent disabled={false} />
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
                    return <option key={exam.id} value={exam.id}>{exam.name}</option>
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
                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                onDrop={this.onDropPDF}
                disabled={isDisabled}
                disablePreview
                multiple
              >
                <DropzoneContent disabled={isDisabled} />
              </Dropzone>

              <br />
              <aside className="menu" style={textStyle}>
                <p className="menu-label">
                  Previously uploaded
              </p>
                <ul className="menu-list">
                  {this.state.selected_exam.pdfs.map(pdf =>
                    <li key={pdf.id}><StatusPDF pdf={pdf} /></li>
                  )}
                </ul>
              </aside>

            </div>
          </div>

        </div>
      </section>

    </div>
  }
}

export default Exams;

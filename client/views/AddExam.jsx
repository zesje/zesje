import React from 'react'
import Dropzone from 'react-dropzone'
import Notification from 'react-bulma-notification'
import { Document, Page } from 'react-pdf/dist/entry.webpack'

import * as api from '../api.jsx'
import Hero from '../components/Hero.jsx'
import DropzoneContent from '../components/DropzoneContent.jsx'

class Exams extends React.Component {
  state = {
    pdf: null,
    previewPageCount: 0,
    exam_name: '',
    types: null,
    selectedType: null
  };

  componentDidMount = () => {
    api.get('/exams/types')
      .then(types => {
        this.setState({ types: types, selectedType: types[0] })
      })
  }

  onChangeType = (index) => {
    const newtype = this.state.types[index]
    if (!newtype.acceptsPDF) {
      this.setState({
        selectedType: newtype,
        pdf: null,
        previewPageCount: 0
      })
    } else {
      this.setState({
        selectedType: newtype
      })
    }
  }

  onDropPDF = (accepted, rejected) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a PDF.')
      return
    }

    this.setState({ pdf: accepted[0] })
  }

  onDocumentLoad = ({ numPages }) => {
    this.setState({
      previewPageCount: Math.min(4, numPages)
    })
  }

  changeInput = (name, regex) => {
    return (event) => {
      this.setState({
        [name]: event.target.value
      })
    }
  }

  onUploadPDF = (event) => {
    if (!this.state.exam_name) {
      Notification.error('Please enter exam name.')
      return
    }
    if (this.state.selectedType.acceptsPDF && !this.state.pdf) {
      Notification.error('Please upload a PDF.')
      return
    }

    const data = new window.FormData()
    data.append('exam_name', this.state.exam_name)
    data.append('layout', this.state.selectedType.value)
    if (this.state.selectedType.acceptsPDF) {
      data.append('pdf', this.state.pdf)
    }
    api.post('exams', data)
      .then(exam => {
        this.props.updateExamList()
        this.props.changeURL('/exams/' + exam.id)
      })
      .catch(resp => {
        resp.json().then(body => Notification.error(body.message))
      })
  }

  render () {
    const previewPages = Array.from({ length: this.state.previewPageCount }, (v, k) => k + 1).map(pageNum => {
      return <div key={'preview_col_' + pageNum} className='column'>
        <Page width={150} height={200}
          renderAnnotations={false} renderTextLayer={false}
          pageNumber={pageNum} />
      </div>
    })
    return (
      <div>

        <Hero title='Add exam' subtitle='first step' />

        <section className='section'>
          <div className='container'>
            <div className='field is-horizontal'>
              <div className='field-label'>
                <label className='label'>Name</label>
              </div>
              <div className='field-body'>
                <div className='field'>
                  <div className='control'>
                    <input
                      className={'input' + (this.state.exam_name ? ' is-success' : ' is-danger')}
                      placeholder='Exam name'
                      value={this.state.exam_name}
                      required
                      onChange={this.changeInput('exam_name')} />
                  </div>
                </div>
              </div>
            </div>

            <div className='field is-horizontal'>
              <div className='field-label'>
                <label className='label'>Type</label>
              </div>
              <div className='field-body'>
                <div className='field'>
                  <div className='control'>
                    <div className='select'>
                      <select onChange={(e) => this.onChangeType(e.target.value)}>
                        {this.state.types !== null ? this.state.types.map((type, index) => {
                          return <option key={`key_${index}`} value={index}>{type.name}</option>
                        }) : null}
                      </select>
                    </div>
                    {this.state.selectedType && <p className='help'>{this.state.selectedType.description}</p>}
                  </div>
                </div>
              </div>
            </div>

            {this.state.selectedType && this.state.selectedType.acceptsPDF &&
              <div className='field is-horizontal'>
                <div className='field-label'>
                  <label className='label'>Upload PDF</label>
                </div>
                <div className='field-body'>
                  <div className='field'>
                    <Dropzone accept='.pdf, application/pdf'
                      activeStyle={{ borderStyle: 'dashed' }}
                      onDrop={this.onDropPDF}
                      disablePreview
                      multiple={false}>
                      <DropzoneContent />
                    </Dropzone>
                    <p className='help'>{this.state.pdf !== null ? this.state.pdf.name : ''}</p>
                  </div>
                </div>
              </div>
            }

            {this.state.pdf != null &&
              <div className='field is-horizontal'>
                <div className='field-label'>
                  <label className='label'>Preview</label>
                </div>
                <div className='field-body'>
                  <div className='field'>
                    <Document
                      file={this.state.pdf}
                      onLoadSuccess={this.onDocumentLoad}
                    >
                      <div className='columns'>
                        {previewPages}
                      </div>
                    </Document>
                  </div>
                </div>
              </div>
            }

            <div className='field is-horizontal'>
              <div className='field-label' />

              <div className='field-body'>
                <div className='field'>
                  <div className='control'>
                    <button
                      className='button is-info'
                      onClick={this.onUploadPDF}
                      disabled={!this.state.exam_name || (this.state.selectedType !== null && this.state.selectedType.acceptsPDF && this.state.pdf === null)}>
                        Create Exam
                    </button>
                  </div>
                </div>
              </div>
            </div>

          </div>

        </section>

      </div >
    )
  }
}

export default Exams

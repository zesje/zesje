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
    examName: '',
    layouts: null,
    selectedLayout: null
  };

  componentDidMount = () => {
    api.get('/exams/layouts')
      .then(layouts => {
        this.setState({ layouts: layouts, selectedLayout: layouts[0] })
      })
  }

  onChangeLayout = (event) => {
    const newtype = this.state.layouts[event.target.value]
    if (!newtype.acceptsPDF) {
      this.setState({
        selectedLayout: newtype,
        pdf: null,
        previewPageCount: 0
      })
    } else {
      this.setState({
        selectedLayout: newtype
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

  addExam = (event) => {
    if (!this.state.examName) {
      Notification.error('Please enter exam name.')
      return
    }
    if (this.state.selectedLayout.acceptsPDF && !this.state.pdf) {
      Notification.error('Please upload a PDF.')
      return
    }

    const data = new window.FormData()
    data.append('exam_name', this.state.examName)
    data.append('layout', this.state.selectedLayout.value)
    if (this.state.selectedLayout.acceptsPDF) {
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
                      className='input'
                      placeholder='Exam name'
                      value={this.state.examName}
                      required
                      onChange={(e) => this.setState({examName: e.target.value})} />
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
                      <select onChange={this.onChangeLayout}>
                        {this.state.layouts !== null ? this.state.layouts.map((layout, index) => {
                          return <option key={`key_${index}`} value={index}>{layout.name}</option>
                        }) : null}
                      </select>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {this.state.selectedLayout &&
              <div className='field is-horizontal'>
                <div className='field-label' />

                <div className='field-body'>
                  <div className='field'>
                    <div className='control'>
                      <p>{this.state.selectedLayout.description}</p>
                    </div>
                  </div>
                </div>
              </div>
            }

            {this.state.selectedLayout && this.state.selectedLayout.acceptsPDF &&
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
                      onClick={this.addExam}
                      disabled={!this.state.examName ||
                        (this.state.selectedLayout !== null && this.state.selectedLayout.acceptsPDF && this.state.pdf === null)}
                    >
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

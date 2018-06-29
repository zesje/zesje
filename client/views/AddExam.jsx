import React from 'react';
import Dropzone from 'react-dropzone'

import Hero from '../components/Hero.jsx';
import DropzoneContent from '../components/DropzoneContent.jsx';

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
PDFJS.workerSrc = true;

import * as api from '../api.jsx'

class Exams extends React.Component {

    state = {
        pdf: null,
        previewPageCount: 0,
        exam_name: '',
    };

    onDropPDF = (accepted, rejected) => {
        if (rejected.length > 0) {
            alert('Please upload a PDF..')
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
            });
        }
    }

    onUploadPDF = (event) => {
        if (!this.state.exam_name) {
            alert('Please enter exam name.')
            return
        }
        if (!this.state.pdf) {
            alert('Please upload a PDF.')
            return
        }
        const data = new FormData()
        data.append('pdf', this.state.pdf)
        data.append('exam_name', this.state.exam_name)
        api.post('exams', data)
            .then(exam => {
                this.props.updateExamList()
                this.props.changeURL('/exams/' + exam.id);
            })
            .catch(resp => {
                resp.json().then(body => alert(body.message))
            })
    }

    render() {
        const previewPages = Array.from({ length: this.state.previewPageCount }, (v, k) => k + 1).map(pageNum => {
            return <div key={'preview_col_' + pageNum} className="column">
                <Page width={150} height={200} renderAnnotations={false} renderTextLayer={false} pageNumber={pageNum} />
            </div>
        })
        return (
            <div>

                <Hero title='Add exam' subtitle="first step" />

                <section className="section">
                    <div className="container">
                        {this.state.pdf != null ? (
                            <div className="column has-text-centered">
                                <h3 className='title'>Preview the PDF</h3>
                                <h5 className='subtitle'>{previewPages.length > 1 ? 'The first ' + previewPages.length + ' pages are shown' : 'The first page is shown'}</h5>
                                <Document
                                    file={this.state.pdf}
                                    onLoadSuccess={this.onDocumentLoad}
                                >
                                    <div className="columns">
                                        {previewPages}
                                    </div>
                                </Document>
                            </div>
                        ) : (
                                <div className="column has-text-centered">
                                    <h3 className='title'>Upload new exam PDF</h3>
                                    <h5 className='subtitle'>a preview will be shown</h5>
                                    <Dropzone accept=".pdf, application/pdf"
                                        style={{}} activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                                        onDrop={this.onDropPDF}
                                        disablePreview
                                        multiple={false}
                                    >
                                        <DropzoneContent />
                                    </Dropzone>
                                </div>
                            )}

                        <div className="control">
                            <input
                                className="input"
                                placeholder="Exam name"
                                value={this.state.exam_name}
                                required={true}
                                onChange={this.changeInput('exam_name')} />
                        </div>
                        <div className="control">
                            <button
                                type="submit"
                                className="is-centered button is-info is-rounded"
                                onClick={this.onUploadPDF}
                            >
                                Upload
                            </button>
                        </div>

                    </div>

                </section>

            </div >
        )
    }
}

export default Exams;

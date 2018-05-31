import React from 'react'
import './GeneratedExamPreview.css';
import * as api from '../api.jsx'

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
/*global PDFJS*/
PDFJS.workerSrc = true;

class GeneratedExamPreview extends React.Component {

    state = {
        examID: null,
        page:  null,
        numPages: null,
        pdfUrl: null,
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.examID != prevState.examID) {
            return {
                examID: newProps.examID
            }
        }
        return null
    }

    componentDidMount() {
        var data = {
            copies: 1,
        }
        api.post('exams/' + this.state.examID + '/generated_pdfs', data)
            .then(() => {
                this.setState({
                    pdfUrl: '/api/exams/' + this.state.examID + '/generated_pdfs/0'
                })
            })
    }

    onPDFLoad = (pdf) => {
        this.setState({
            page: 0,
            numPages: pdf.numPages,
        })
    }

    setPage = (newPage) => {
        this.setState((prevState) => {
            return {
                // clamp the page
                selectedWidget: null,
                page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
            }
        })
    }

    prevPage = () => {
        this.setPage(this.state.page - 1)
    }

    nextPage = () => {
        this.setPage(this.state.page + 1)
    }

    render = () => {
        return (
            <React.Fragment>
                <nav className='level'>
                    <div className='level-item'>
                        <div className='field has-addons is-mobile'>
                            <div className='control'>
                                <button
                                    type='submit'
                                    className='button is-link is-rounded'
                                    onClick={this.prevPage}>Previous</button>
                            </div>
                            <div className='control'>
                                <div className="field-text is-rounded has-text-centered is-link">
                                    {'Page ' + (this.state.page + 1) + ' of ' + this.state.numPages}
                                </div>
                            </div>
                            <div className='control'>
                                <button
                                    type='submit'
                                    className='button is-link is-rounded'
                                    onClick={this.nextPage}>Next</button>
                            </div>
                        </div>
                    </div>
                </nav>
                <div className={'columns is-centered'}>
                    <Document
                        className={'column is-narrow'}
                        file={this.state.pdfUrl}
                        onLoadSuccess={this.onPDFLoad}
                    >
                        <Page
                            renderAnnotations={false}
                            renderTextLayer={false}
                            pageIndex={this.state.page}
                            onMouseDown={this.handleMouseDown} />
                    </Document>
                </div>
            </React.Fragment>
        )
    }

}

GeneratedExamPreview.defaultProps = {

}

export default GeneratedExamPreview

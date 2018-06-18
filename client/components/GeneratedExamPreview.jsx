import React from 'react'
import * as api from '../api.jsx'
import EmptyPDF from '../components/EmptyPDF.jsx'

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
/*global PDFJS*/
PDFJS.workerSrc = true;

class GeneratedExamPreview extends React.Component {

    state = {
        pdfUrl: null,
    }

    componentDidMount() {
        let data = {
            copies: 1,
        }
        api.post('exams/' + this.props.examID + '/generated_pdfs', data)
            .then(() => {
                this.setState({
                    pdfUrl: '/api/exams/' + this.props.examID + '/generated_pdfs/0'
                })
            })
    }

    render = () => {
        return (
            <Document
                file={this.state.pdfUrl}
                onLoadSuccess={this.props.onPDFLoad}
                loading={<EmptyPDF />}
                noData={<EmptyPDF />}
            >
                <Page
                    renderAnnotations={false}
                    renderTextLayer={false}
                    pageIndex={this.props.page} />
            </Document>
        )
    }
}

GeneratedExamPreview.defaultProps = {

}

export default GeneratedExamPreview

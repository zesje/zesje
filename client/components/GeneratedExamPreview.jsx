import React from 'react'
import EmptyPDF from '../components/EmptyPDF.jsx'

import { Document, Page } from 'react-pdf/dist/entry.webpack'

class GeneratedExamPreview extends React.Component {
  render = () => {
    return (
      <Document
        file={'/api/exams/' + this.props.examID + '/preview'}
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

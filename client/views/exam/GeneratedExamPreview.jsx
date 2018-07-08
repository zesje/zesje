import React from 'react'
import { Document, Page } from 'react-pdf/dist/entry.webpack'

import EmptyPDF from './EmptyPDF.jsx'

class GeneratedExamPreview extends React.Component {
  render = () => {
    return (
      <Document
        file={'/api/exams/' + this.props.examID + '/preview'}
        onLoadSuccess={this.props.onPDFLoad}
        loading={<EmptyPDF />}
        noData={<EmptyPDF />} >
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

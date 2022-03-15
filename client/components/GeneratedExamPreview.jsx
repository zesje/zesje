import React from 'react'
import { EmptyPDF, ErrorPDF } from '../components/PDFPlaceholders.jsx'

import { Document, Page } from 'react-pdf/dist/esm/entry.webpack'

class GeneratedExamPreview extends React.Component {
  render = () => {
    return (
      <Document
        file={'/api/exams/' + this.props.examID + '/preview'}
        onLoadSuccess={this.props.onPDFLoad}
        loading={<EmptyPDF />}
        error={<ErrorPDF />}
        noData={<ErrorPDF text={'No PDF file specified.'} />}
      >
        <Page
          renderAnnotations={false}
          renderTextLayer={false}
          pageIndex={this.props.page}
        />
      </Document>
    )
  }
}

GeneratedExamPreview.defaultProps = {

}

export default GeneratedExamPreview

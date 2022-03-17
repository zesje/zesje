import React from 'react'

import Spinner from './Img.jsx'

const formatToSize = (format) => {
  switch (format) {
    case 'a4':
    case 'A4':
    default:
      return { width: 595, height: 841 }
  }
}

export const EmptyPDF = ({ format = 'a4', children }) => {
  const size = formatToSize(format)

  return (
    <div
      style={{
        paddingTop: '4rem',
        minWidth: size.width + 'px',
        minHeight: size.height + 'px',
        backgroundColor: 'white'
      }}
      className='has-text-centered'
    >
      { children }
    </div>
  )
}

export const LoadingPDF = ({
  format = 'a4',
  color = 'info'
}) => <EmptyPDF><Spinner color={color} /></EmptyPDF>

export const ErrorPDF = ({
  format = 'a4',
  text = 'An error was produced while loading the PDF, try reloading the page.'
}) => <EmptyPDF><div className='notification is-danger has-text-centered'>{ text }</div></EmptyPDF>

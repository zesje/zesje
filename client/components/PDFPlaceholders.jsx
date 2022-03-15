import React from 'react'

import { Spinner } from './Img.jsx'

const formatToSize = (format) => {
  switch (format) {
    case 'a4':
    case 'A4':
    default:
      return { width: 595, height: 841 }
  }
}

export const EmptyPDF = ({ format, color = 'info', children }) => {
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
      { children || <Spinner />}
    </div>
  )
}

export const ErrorPDF = ({ format, color = 'info', text }) => {
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
      <div className='notification is-danger has-text-centered'>
        { text || 'An error was produced while loading the PDF, try reloading the page.' }
      </div>
    </div>
  )
}

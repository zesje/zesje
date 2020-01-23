import React from 'react'

const PDFOverlay = (props) => {
  let width
  let height
  switch (props.format) {
    case 'a4':
    case 'A4':
    default:
      width = 595
      height = 841
  }

  let mmPerInch = 25.4
  let ptPerInch = 72

  let marginMm = 10
  let marginPt = marginMm / mmPerInch * ptPerInch
  let lengthMm = 8
  let lengthPt = lengthMm / mmPerInch * ptPerInch
  let widthPt = 1

  const style = {
    position: 'absolute',
    top: 0,
    pointerEvents: 'none'
  }
  const lineStyle = {
    stroke: 'black',
    strokeWidth: widthPt
  }

  return (
    <svg width={width} height={height} style={style} >
      {/* top left */}
      <line x1={marginPt} y1={marginPt} x2={marginPt + lengthPt} y2={marginPt} style={lineStyle} />
      <line x1={marginPt} y1={marginPt} x2={marginPt} y2={marginPt + lengthPt} style={lineStyle} />
      {/* top right */}
      <line x1={width - marginPt} y1={marginPt} x2={width - marginPt - lengthPt} y2={marginPt} style={lineStyle} />
      <line x1={width - marginPt} y1={marginPt} x2={width - marginPt} y2={marginPt + lengthPt} style={lineStyle} />
      {/* bottom left */}
      <line x1={marginPt} y1={height - marginPt} x2={marginPt + lengthPt} y2={height - marginPt} style={lineStyle} />
      <line x1={marginPt} y1={height - marginPt} x2={marginPt} y2={height - marginPt - lengthPt} style={lineStyle} />
      {/* bottom right */}
      <line x1={width - marginPt} y1={height - marginPt} x2={width - marginPt - lengthPt} y2={height - marginPt} style={lineStyle} />
      <line x1={width - marginPt} y1={height - marginPt} x2={width - marginPt} y2={height - marginPt - lengthPt} style={lineStyle} />
    </svg>
  )
}

export default PDFOverlay

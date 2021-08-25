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

  const mmPerInch = 25.4
  const ptPerInch = 72

  const marginMm = 10
  const marginPt = marginMm / mmPerInch * ptPerInch
  const lengthMm = 8
  const lengthPt = lengthMm / mmPerInch * ptPerInch
  const widthPt = 1

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
    <svg width={width} height={height} style={style}>
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
      <line x1={width - marginPt} y1={height - marginPt} x2={width - marginPt - lengthPt} y2={height - marginPt}
        style={lineStyle} />
      <line x1={width - marginPt} y1={height - marginPt} x2={width - marginPt} y2={height - marginPt - lengthPt}
        style={lineStyle} />
    </svg>
  )
}

export default PDFOverlay

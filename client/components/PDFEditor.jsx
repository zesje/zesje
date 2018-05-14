import React from 'react';

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
PDFJS.workerSrc = true;

import Draggable from 'react-draggable';

const editorStyle = {
    display: 'flex',
    // justifyContent: 'space-around',
    backgroundColor: '#ddd'
};

const widgetStyle = {
    background: '#fff',
    border: '1px solid #999',
    borderRadius: '3px',
    width: '180px',
    height: '180px',
    margin: '0px',
    padding: '0px',
    top: '0px',
    left: '0px',
    position: 'absolute',
}

class PDFEditor extends React.Component {

    state = {
        mouseDown: false,
        selectionStartPoint: null,
        selectionEndPoint: null,
        selectionBox: null,
        examID: null,
        page: 1,
        widgets: []
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.examID != prevState.examID) {
            return {
                examID: newProps.examID
            }
        }
        return null
    }

    handleMouseDown = (e) => {
        if (e.button === 2 || e.nativeEvent.which === 2) {
            return
        }
        this.setState({
            mouseDown: true,
            selectionStartPoint: {
                x: e.pageX,
                y: e.pageY
            }
        });

        window.document.addEventListener('mousemove', this.handleMouseMove)
        window.document.addEventListener('mouseup', this.handleMouseUp)
    }

    handleMouseUp = (e) => {
        window.document.removeEventListener('mousemove', this.handleMouseMove)
        window.document.removeEventListener('mouseup', this.handleMouseUp)
        const selectionBox = this.state.selectionBox
        this.setState({
            mouseDown: false,
            selectionStartPoint: null,
            selectionEndPoint: null,
            selectionBox: null
        })
        this.setState({
            widgets:[...this.state.widgets, {
                startPosition: {
                    left: selectionBox.left,
                    top: selectionBox.top,
                    width: selectionBox.width,
                    height: selectionBox.height,
                }
            }]
        })
    }

    /**
    * On document element mouse move
    */
    handleMouseMove = (e) => {
        e.preventDefault();
        if (this.state.mouseDown) {
            const selectionEndPoint = {
                x: e.pageX,
                y: e.pageY
            }
            this.setState({
                selectionEndPoint: selectionEndPoint,
                selectionBox: this.calculateSelectionBox(this.state.selectionStartPoint, selectionEndPoint)
            })
        }
    }

    /**
     * Calculate selection box dimensions
     *
     * TODO: Clamp values to parent
     */
    calculateSelectionBox = (selectionStartPoint, selectionEndPoint) => {
        if (!this.state.mouseDown || selectionEndPoint === null || selectionStartPoint === null) {
            return null
        }
        const parentNode = this.refs.selectionArea
        const left = Math.min(selectionStartPoint.x, selectionEndPoint.x) - parentNode.offsetLeft
        const top = Math.min(selectionStartPoint.y, selectionEndPoint.y) - parentNode.offsetTop
        const width = Math.abs(selectionStartPoint.x - selectionEndPoint.x)
        const height = Math.abs(selectionStartPoint.y - selectionEndPoint.y)
        const result = {
            left: left,
            top: top,
            width: width,
            height: height,

            background: 'rgba(0, 162, 255, 0.4)',
            position: 'absolute',
            zIndex: 99,
        }
        return result
    }

    renderSelectionBox = () => {
        if (!this.state.mouseDown || this.state.selectionEndPoint === null || this.state.selectionStartPoint === null) {
            return null
        } else {
            return(
                <div className='selection-border' style={this.state.selectionBox}></div>
            )
        }
    }

    render() {

        const dragHandlers = {onStart: this.onStart, onStop: this.onStop};

        var cnt = 0
        const draggables = this.state.widgets.map(widget => {
            return <Draggable key={'widget_' + cnt++} {...dragHandlers} bounds="parent">
              <div style={{...widgetStyle, ...{
                  left: widget.startPosition.left,
                  top: widget.startPosition.top,
                  width: widget.startPosition.width,
                  height: widget.startPosition.height,
              }}}>
                This is a cool widget
              </div>
            </Draggable>
        })
        return (
            <div ref="selectionArea" style={editorStyle}>
                <div style={{display: 'inline-block'}}>
                    <Document
                        onLoadSuccess={this.onDocumentLoad}
                        file={(this.state.examID && "/api/exam_pdfs/" + this.state.examID) || null}
                        style={{position: 'relative'}}
                    >
                        <Page
                            renderAnnotations={false}
                            renderTextLayer={false}
                            pageNumber={this.state.page}
                            onMouseDown={this.handleMouseDown} />
                            {this.renderSelectionBox()}
                    </Document>
                    {draggables}
                </div>
            </div>
        )
    }

}

export default PDFEditor

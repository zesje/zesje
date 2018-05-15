import React from 'react';

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
PDFJS.workerSrc = true;

import update from 'immutability-helper';
import Draggable from 'react-draggable';

const editorStyle = {
    display: 'flex',
    position: 'relative',
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
        page: null,
        numPages: null,
        widgets: null
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.examID != prevState.examID) {
            return {
                examID: newProps.examID
            }
        }
        return null
    }

    onPDFLoad = (pdf) => {
        this.setState({
            page: 1,
            numPages: pdf.numPages,
            // initialize array to size of pdf
            widgets: Array.from(Array(pdf.numPages), () => new Array()),
        })
    }

    setPage = (newPage) => {
        this.setState({
            // clamp the page
            page: Math.max(1, Math.min(newPage, this.state.numPages))
        })
    }

    prevPage = (e) => {
        this.setPage(this.state.page - 1)
    }

    nextPage = (e) => {
        this.setPage(this.state.page + 1)
    }

    handleMouseDown = (e) => {
        if (e.button === 2 || e.nativeEvent.which === 2) {
            return
        }
        this.setState({
            mouseDown: true,
            selectionStartPoint: this.getCoordinatesForEvent(e)
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
        if (selectionBox) {
            this.setState({
                widgets: update(this.state.widgets, {
                    [this.state.page - 1]: {
                        $push: [{
                            x: selectionBox.left,
                            y: selectionBox.top,
                            width: selectionBox.width,
                            height: selectionBox.height,
                        }]
                    }
                })
            })
        }
    }

    /**
    * On document element mouse move
    */
    handleMouseMove = (e) => {
        e.preventDefault();
        if (this.state.mouseDown) {
            const selectionEndPoint = this.getCoordinatesForEvent(e)
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

        const left = Math.min(selectionStartPoint.x, selectionEndPoint.x)
        const top = Math.min(selectionStartPoint.y, selectionEndPoint.y)
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
        if (this.state.mouseDown && this.state.selectionEndPoint && this.state.selectionStartPoint) {
            return(
                <div className='selection-border' style={this.state.selectionBox}></div>
            )
        } else {
            return null
        }
    }

    getCoordinatesForEvent = (e) => {
        const parentNode = this.refs.selectionArea
        // const cumulativeOffset = this.calculateCumulativeOffsetForElement(parentNode)
        const cumulativeOffset = this.cumulativeOffset(parentNode)
        const scrollY = Math.abs(parentNode.getClientRects()[0].top - cumulativeOffset.top)
        const scrollX = Math.abs(parentNode.getClientRects()[0].left - cumulativeOffset.left)
        return {
            x: e.clientX - cumulativeOffset.left + scrollX,
            y: e.clientY - cumulativeOffset.top + scrollY
        };
    }

    cumulativeOffset = (el) => {
        var top = 0
        var left = 0

        // No tail-call optimization so this is fine
        while (el) {
            top  += el.offsetTop  || 0
            left += el.offsetLeft || 0
            el    = el.offsetParent
        }

        return {
            top: top,
            left: left
        }
    }

    setWidgetPosition = (page, index, x, y) => {
        this.setState({
            widgets: update(this.state.widgets,{
                [page - 1]: {
                    [index]: {
                        x: {$set: x},
                        y: {$set: y}
                    }
                }
            })
        })
    }

    renderWidgets = () => {
        if (this.state.widgets) {
            const page = this.state.page
            const widgets = this.state.widgets[page - 1]
            return widgets.map((widget, index) => {
                return (
                    <Draggable
                        position={{x: widget.x, y: widget.y}}
                        bounds="parent"
                        key={'widget_' + page + '_' + index}
                        onStop={(_, data) => this.setWidgetPosition(page, index, data.x, data.y)}
                    >
                        <div
                            style={{...widgetStyle, ...{
                                width: widget.width,
                                height: widget.height,
                            }}}
                        >
                            This is a cool widget
                        </div>
                    </Draggable>
                )
            })
        } else {
            return null
        }

    }

    render() {
        const widgets = this.renderWidgets()
        return (
            <div className='editorArea columns' style={editorStyle} >
                <div ref="selectionArea" className='SelectionArea column' >
                    <Document
                        file={(this.state.examID && "/api/exam_pdfs/" + this.state.examID) || null}
                        onLoadSuccess={this.onPDFLoad}
                        style={{position: 'relative'}}
                    >
                        <Page
                            renderAnnotations={false}
                            renderTextLayer={false}
                            pageNumber={this.state.page}
                            onMouseDown={this.handleMouseDown} />
                    </Document>
                    {widgets}
                    {this.renderSelectionBox()}
                </div>
                <div className="column">
                    <div className="level">
                        <div className="level-item">
                            <div className="field has-addons is-mobile">
                                <div className="control">
                                    <button
                                        type='submit'
                                        className="button is-link is-rounded"
                                        onClick={this.prevPage}>Previous</button>
                                </div>
                                <div className="control">
                                    <span className="input has-text-centered">Page {this.state.page} of {this.state.numPages}</span>
                                </div>
                                <div className="control">
                                    <button
                                        type="submit"
                                        className="button is-link is-rounded"
                                        onClick={this.nextPage}>Next</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

}

export default PDFEditor

import React from 'react';
import './PDFEditor.css';

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
PDFJS.workerSrc = true;

import update from 'immutability-helper';
import ResizeAndDrag from 'react-rnd'

class PDFEditor extends React.Component {

    state = {
        mouseDown: false,
        selectionStartPoint: null,
        selectionEndPoint: null,
        selectionBox: null,
        examID: null,
        page: null,
        numPages: null,
        widgets: null,
        selectedWidget: null,
    }

    static getDerivedStateFromProps = (newProps, prevState) => {
        if (newProps.examID != prevState.examID) {
            return {
                examID: newProps.examID
            }
        }
        return null
    }

    getPDFUrl = () => {
        return (this.state.examID && "/api/exam_pdfs/" + this.state.examID) || null
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
            selectedWidget: null,
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
            if (selectionBox.width >= this.props.widgetMinWidth && selectionBox.height >= this.props.widgetMinHeight) {
                this.setState({
                    selectedWidget: this.state.widgets[this.state.page - 1].length,
                    widgets: update(this.state.widgets, {
                        [this.state.page - 1]: {
                            $push: [{
                                x: selectionBox.left,
                                y: selectionBox.top,
                                width: selectionBox.width,
                                height: selectionBox.height,
                                name: '',
                            }]
                        }
                    })
                })
            }
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

            background:
                width >= this.props.widgetMinWidth &&
                height >= this.props.widgetMinHeight ?
                    'rgba(100, 255, 100, 0.4)'
                :
                    'rgba(255, 100, 100, 0.4)',
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

    renderWidgets = () => {
        if (this.state.widgets) {
            const page = this.state.page
            const widgets = this.state.widgets[page - 1]
            return widgets.map((widget, index) => {
                return (
                    <ResizeAndDrag
                        key={'widget_' + page + '_' + index}
                        bounds='parent'
                        minWidth={this.props.widgetMinWidth}
                        minHeight={this.props.widgetMinHeight}
                        position={{
                            x: widget.x,
                            y: widget.y,
                        }}
                        size={{
                            width: widget.width,
                            height: widget.height,
                        }}
                        onResize={(e, direction, ref, delta, position) => {
                            this.setState({
                                widgets: update(this.state.widgets,{
                                    [page - 1]: {
                                        [index]: {
                                            width: {$set: ref.offsetWidth},
                                            height: {$set: ref.offsetHeight},
                                            x: {$set: position.x},
                                            y: {$set: position.y},
                                        }
                                    }
                                })
                            })
                        }}
                        onDragStart={() => {
                            this.setState({
                                selectedWidget: index,
                            })
                        }}
                        onDragStop={(e, d) => {
                            this.setState({
                                widgets: update(this.state.widgets,{
                                    [page - 1]: {
                                        [index]: {
                                            x: {$set: d.x},
                                            y: {$set: d.y},
                                        }
                                    }
                                })
                            })
                        }}
                    >
                        <div
                            className='widget'
                        >
                            This is a cool widget
                        </div>
                    </ResizeAndDrag>

                )
            })
        } else {
            return null
        }
    }

    handleWidgetNameChange = (page, index) => {
        return (e) => {
            this.setState({
                widgets: update(this.state.widgets, {
                    [page - 1]: {
                        [index]: {
                            name: {$set: e.target.value},
                        }
                    }
                })
            })
        }
    }

    renderWidgetDetails = () => {
        const widgets = this.state.widgets
        const page = this.state.page
        const selectedWidget = this.state.selectedWidget
        if (widgets && page && selectedWidget !== null
                && widgets[page - 1]
                && widgets[page - 1][selectedWidget]) {
            const widget = widgets[page - 1][selectedWidget]
            console.log(widget.name)
            return (
                <nav className="panel">
                    <p className="panel-heading">
                        Question details
                    </p>
                    <div className="panel-block">
                        Position: ({widget.x},{widget.y})<br />
                        Size: {widget.width}x{widget.height}<br />
                    </div>
                    <div className="panel-block">
                        <div className="field">
                            <label className="label">Name</label>
                            <div className="control">
                                <input
                                    className="input"
                                    type="text"
                                    placeholder="Question name"
                                    value={widget.name}
                                    onChange={this.handleWidgetNameChange(page, selectedWidget)}
                                />
                            </div>
                        </div>
                    </div>
                </nav>
            )
        } else {
            return null
        }
    }

    render() {
        const widgets = this.renderWidgets()
        return (
            <div className='editor-area columns' >
                <div className='column' >
                    <div ref="selectionArea" className='selection-area' >
                        <Document
                            file={this.getPDFUrl()}
                            onLoadSuccess={this.onPDFLoad}
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

                    {this.renderWidgetDetails()}

                </div>
            </div>
        )
    }

}

PDFEditor.defaultProps = {
    widgetMinWidth: 75,
    widgetMinHeight: 50,
}

export default PDFEditor

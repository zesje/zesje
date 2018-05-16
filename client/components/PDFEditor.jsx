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
            page: 0,
            numPages: pdf.numPages,
            // initialize array to size of pdf
            widgets: Array.from(Array(pdf.numPages), () => new Array()),
        })
    }

    setPage = (newPage) => {
        this.setState({
            // clamp the page
            selectedWidget: null,
            page: Math.max(0, Math.min(newPage, this.state.numPages - 1))
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
                    selectedWidget: this.state.widgets[this.state.page].length,
                    widgets: update(this.state.widgets, {
                        [this.state.page]: {
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
            const widgets = this.state.widgets[page]
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
                                    [page]: {
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
                                    [page]: {
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
                    [page]: {
                        [index]: {
                            name: {$set: e.target.value},
                        }
                    }
                })
            })
        }
    }

    handleWidgetDeletion = (page, index, prompt = true) => {
        const widgets = this.state.widgets
        if (widgets && page && index !== null
                && widgets[page]
                && widgets[page][index]) {
            const widget = widgets[page][index]
            if (prompt && confirm('Are you sure you want to delete this widget?')) {
                this.setState({
                    selectedWidget: null,
                    widgets: update(this.state.widgets, {
                        [this.state.page]: {
                            $splice: [[index, 1]]
                        }
                    })

                })
            }
        }
    }

    renderWidgetDetails = () => {
        const widgets = this.state.widgets
        const page = this.state.page
        const selectedWidget = this.state.selectedWidget
        if (widgets && page !== null && selectedWidget !== null
                && widgets[page]
                && widgets[page][selectedWidget]) {
            const widget = widgets[page][selectedWidget]
            console.log(widget.name)
            return (
                <nav className="panel">
                    <p className="panel-heading">
                        Widget details
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
                    <div className="panel-block">
                        <div className="field">
                            <label className="label">Actions</label>
                            <div className="control">
                                <button
                                    className="button is-danger"
                                    onClick={() => this.handleWidgetDeletion(page, selectedWidget)}
                                >
                                    Delete
                                </button>
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
        const widgetDetails = this.renderWidgetDetails()
        return (
            <div className='editor-area columns is-centered' >
                <div className='column is-narrow'  >
                    <div ref="selectionArea" className='selection-area' >
                        <Document
                            file={this.getPDFUrl()}
                            onLoadSuccess={this.onPDFLoad}
                        >
                            <Page
                                renderAnnotations={false}
                                renderTextLayer={false}
                                pageNumber={this.state.page + 1}
                                onMouseDown={this.handleMouseDown} />
                        </Document>
                        {widgets}
                        {this.renderSelectionBox()}
                    </div>
                </div>
                <div className='column is-narrow editor-side-panel' >
                    <div className='field has-addons is-mobile'>
                        <div className='control'>
                            <button
                                type='submit'
                                className='button is-link is-rounded'
                                onClick={this.prevPage}>Previous</button>
                        </div>
                        <div className='control'>
                            <span className='input is-static has-text-centered'>Page {this.state.page + 1} of {this.state.numPages}</span>
                        </div>
                        <div className='control'>
                            <button
                                type='submit'
                                className='button is-link is-rounded'
                                onClick={this.nextPage}>Next</button>
                        </div>
                    </div>

                    {widgetDetails ? widgetDetails : (
                        <nav className="panel">
                            <p className="panel-heading">
                                Widget details
                            </p>
                            <div className="panel-block">
                                Select a widget to modify its details
                            </div>
                        </nav>
                    )}

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

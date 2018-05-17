import React from 'react';
import './PDFEditor.css';
import * as api from '../api.jsx'

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
        })
        this.updateWidgets()
    }

    updateWidgets = (andThen) => {
        api.get('exams/' + this.state.examID)
            .then(exam => {
                // initialize array to size of pdf
                const widgets = Array.from(Array(this.state.numPages), () => new Array())
                exam.widgets.forEach((widget) => {
                    const data = JSON.parse(widget.data)
                    widgets[data.page].push({
                        id: widget.id,
                        x: data.x,
                        y: data.y,
                        width: data.width,
                        height: data.height,
                    })
                })
                this.setState({
                    widgets: widgets
                })
            })
            .then(andThen)
    }

    setPage = (newPage) => {
        this.setState((prevState, props) => {
            return {
                // clamp the page
                selectedWidget: null,
                page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
            }
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
            selectedWidget: null,
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
                const widgetData = {
                    page: this.state.page,
                    x: selectionBox.left,
                    y: selectionBox.top,
                    width: selectionBox.width,
                    height: selectionBox.height,
                    name: null,
                }
                const formData = new FormData()
                formData.append('exam_id', this.state.examID)
                formData.append('data', JSON.stringify(widgetData))
                api.post('widgets', formData).then(widget => {
                    widgetData.id = widget.id
                    this.setState((prevState, props) => {
                        return {
                            selectedWidget: prevState.widgets[prevState.page].length,
                            widgets: update(prevState.widgets, {
                                [prevState.page]: {
                                    $push: [widgetData]
                                }
                            })
                        }
                    })
                }).catch(err => {
                    console.log(err)
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
            this.setState((prevState, props) => {
                return {
                    selectionEndPoint: selectionEndPoint,
                    selectionBox: this.calculateSelectionBox(prevState.selectionStartPoint, selectionEndPoint)
                }
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
                            this.handleWidgetUpdate(page, index, {
                                width: {$set: ref.offsetWidth},
                                height: {$set: ref.offsetHeight},
                                x: {$set: position.x},
                                y: {$set: position.y},
                            }, false)
                        }}
                        onResizeStop={(e, direction, ref, delta, position) => {
                            this.handleWidgetUpdate(page, index, {
                                width: {$set: ref.offsetWidth},
                                height: {$set: ref.offsetHeight},
                                x: {$set: position.x},
                                y: {$set: position.y},
                            })
                        }}
                        onDragStart={() => {
                            this.setState({
                                selectedWidget: index,
                            })
                        }}
                        onDragStop={(e, d) => {
                            this.handleWidgetUpdate(page, index, {
                                x: {$set: d.x},
                                y: {$set: d.y},
                            })
                        }}
                    >
                        <div
                            className='widget'
                        >
                            {widget.name}
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
            const value = e.target.value
            this.setState((prevState, props) => {
                return {
                    widgets: update(prevState.widgets, {
                        [page]: {
                            [index]: {
                                name: {$set: value},
                            }
                        }
                    })
                }
            })
        }
    }

    getWidgetSafe = (page, widget) => {
        const widgets = this.state.widgets
        if (widgets && page !== null && widget !== null
                && widgets[page]
                && widgets[page][widget]) {
            return widgets[page][widget]
        } else {
            return null
        }
    }

    handleWidgetDeletion = (page, index, prompt = true) => {
        const widget = this.getWidgetSafe(page, index)
        if (widget) {
            if (prompt && confirm('Are you sure you want to delete this widget?')) {
                api.del('widgets/' + widget.id)
                    .then(resp => {
                        this.setState((prevState, props) => {
                            return {
                                selectedWidget: null,
                                widgets: update(prevState.widgets, {
                                    [prevState.page]: {
                                        $splice: [[index, 1]]
                                    }
                                })
                            }
                        })
                    })
                    .catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateWidgets()
                    })
            }
        }
    }

    handleWidgetUpdate = (page, index, newData, putToServer = true) => {
        // Now only relevant to update the data property
        // check if widget really exists
        if (this.getWidgetSafe(page, index)) {
            this.setState((prevState, props) => {
                return {
                    widgets: update(prevState.widgets, {
                        [page]: {
                            [index]: newData
                        }
                    })
                }
            }, () => {
                if (putToServer) {
                    // make sure to fetch widget from updated state
                    const widget = this.getWidgetSafe(page, index)
                    // construct whole new data object as it is opaque to the
                    // server and we're using http PUT
                    api.put('widgets/' + widget.id + '/data', {
                        page: page,
                        x: widget.x,
                        y: widget.y,
                        width: widget.width,
                        height: widget.height,
                        name: widget.name,
                    }).then(resp => {
                        console.log(resp)
                    }).catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateWidgets()
                    })
                }
            })
        }
    }

    renderWidgetDetails = () => {
        const {
            page,
            selectedWidget} = this.state
        const widget = this.getWidgetSafe(
            this.state.page,
            this.state.selectedWidget)
        if (widget) {
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
                                    value={widget.name || ''}
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

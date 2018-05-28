import React from 'react';
import './PDFEditor.css';
import barcodeExampleImage from './barcode_example.png'
import studentIdExampleImage from './student_id_example.png'
import * as api from '../api.jsx'

import { Document, Page } from 'react-pdf';
// worker is prefered but need to convince webpack to cooperate
/*global PDFJS*/
PDFJS.workerSrc = true;

/*global window*/
/*global FormData*/
/*global confirm*/

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
        barcodeWidget: null,
        studentIdWidget: null,
        selectedWidgetIndex: null,
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
        return (this.state.examID && "/api/exams/" + this.state.examID + '/source_pdf') || null
    }

    onPDFLoad = (pdf) => {
        this.setState({
            page: 0,
            numPages: pdf.numPages,
        })
        this.updateExam()
    }

    updateExam = () => {
        api.get('exams/' + this.state.examID)
            .then(exam => {
                // initialize array to size of pdf
                const problemWidgets = exam.problems.map(problem => {
                    // keep page and name of problem as widget.problem object
                    return {
                        ...problem.widget,
                        problem: {
                            id: problem.id,
                            page: problem.page,
                            name: problem.name,
                        },
                    }
                })
                const widgets = problemWidgets.concat(exam.widgets)
                this.setState({
                    widgets: widgets
                })
            })
    }

    setPage = (newPage) => {
        this.setState((prevState) => {
            return {
                // clamp the page
                selectedWidgetIndex: null,
                page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
            }
        })
    }

    prevPage = () => {
        this.setPage(this.state.page - 1)
    }

    nextPage = () => {
        this.setPage(this.state.page + 1)
    }

    handleMouseDown = (e) => {
        if (e.button === 2 || e.nativeEvent.which === 2) {
            return
        }
        this.setState({
            selectedWidgetIndex: null,
            mouseDown: true,
            selectionStartPoint: this.getCoordinatesForEvent(e)
        });

        window.document.addEventListener('mousemove', this.handleMouseMove)
        window.document.addEventListener('mouseup', this.handleMouseUp)
    }

    handleMouseUp = () => {
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
            if (selectionBox.width >= this.props.problemMinWidth && selectionBox.height >= this.props.problemMinHeight) {
                const problemData = {
                    name: 'New problem', // TODO: Name
                    page: this.state.page,
                }
                const widgetData = {
                    x: Math.round(selectionBox.left),
                    y: Math.round(selectionBox.top),
                    width: Math.round(selectionBox.width),
                    height: Math.round(selectionBox.height),
                }
                const formData = new FormData()
                formData.append('exam_id', this.state.examID)
                formData.append('name', problemData.name)
                formData.append('page', problemData.page)
                formData.append('x', widgetData.x)
                formData.append('y', widgetData.y)
                formData.append('width', widgetData.width)
                formData.append('height', widgetData.height)
                api.post('problems', formData).then(result => {
                    widgetData.id = result.widget_id
                    problemData.id = result.id
                    widgetData.problem = problemData
                    this.setState((prevState) => {
                        return {
                            selectedWidgetIndex: prevState.widgets.length,
                            widgets: update(prevState.widgets, {
                                $push: [widgetData]
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
            this.setState((prevState) => {
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
                width >= this.props.problemMinWidth &&
                height >= this.props.problemMinHeight ?
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
        const parentNode = this.selectionArea
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
            const {
                page,
                widgets,
            } = this.state
            var minWidth
            var minHeight
            var view
            var enableResizing

            return widgets.map((widget, index) => {
                if (widget.problem && widget.problem.page !== page) {
                    return null
                }

                const isSelected = index == this.state.selectedWidgetIndex

                if (widget.problem) {
                    minWidth = this.props.problemMinWidth
                    minHeight = this.props.problemMinHeight
                    view = (
                        <div
                            className={isSelected ? 'widget selected' : 'widget'}
                        />
                    )
                    enableResizing = true
                } else {
                    minWidth = 0
                    minHeight = 0
                    var image
                    if (widget.name == 'barcode_widget') {
                        image = barcodeExampleImage
                    } else if (widget.name == 'student_id_widget') {
                        image = studentIdExampleImage
                    }
                    view = (
                        <div
                            className={isSelected ? 'widget selected' : 'widget'}
                            style={{
                                boxSizing: 'content-box',
                                backgroundImage: 'url(' + image + ')',
                                backgroundRepeat: 'no-repeat',
                            }}
                        />
                    )
                    enableResizing = false
                }
                return (
                    <ResizeAndDrag
                        key={'widget_' + widget.id}
                        bounds='parent'
                        minWidth={minWidth}
                        minHeight={minHeight}
                        enableResizing={{
                            bottom: enableResizing,
                            bottomLeft: enableResizing,
                            bottomRight: enableResizing,
                            left: enableResizing,
                            right: enableResizing,
                            top: enableResizing,
                            topLeft: enableResizing,
                            topRight: enableResizing,
                        }}
                        position={{
                            x: widget.x,
                            y: widget.y,
                        }}
                        size={{
                            width: widget.width,
                            height: widget.height,
                        }}
                        onResize={(e, direction, ref, delta, position) => {
                            this.handleWidgetUpdate(index, {
                                width: {$set: ref.offsetWidth},
                                height: {$set: ref.offsetHeight},
                                x: {$set: position.x},
                                y: {$set: position.y},
                            }, false)
                        }}
                        onResizeStop={(e, direction, ref, delta, position) => {
                            this.handleWidgetUpdate(index, {
                                width: {$set: ref.offsetWidth},
                                height: {$set: ref.offsetHeight},
                                x: {$set: position.x},
                                y: {$set: position.y},
                            })
                        }}
                        onDragStart={() => {
                            this.setState({
                                selectedWidgetIndex: index,
                            })
                        }}
                        onDragStop={(e, d) => {
                            this.handleWidgetUpdate(index, {
                                x: {$set: d.x},
                                y: {$set: d.y},
                            })
                        }}
                    >
                        {view}
                    </ResizeAndDrag>
                )
            })
        }
    }

    handleWidgetDeletion = (index, prompt = true) => {
        const widget = this.state.widgets[index]
        if (widget) {
            if (prompt && confirm('Are you sure you want to delete this widget?')) {
                api.del('widgets/' + widget.id)
                    .then(() => {
                        this.setState((prevState) => {
                            return {
                                selectedWidgetIndex: null,
                                widgets: update(prevState.widgets, {
                                    $splice: [[index, 1]]
                                })
                            }
                        })
                    })
                    .catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateExam()
                    })
            }
        }
    }

    handleWidgetUpdate = (index, newData, putToServer = true) => {
        // Now only relevant to update the data property
        // check if widget really exists
        if (this.state.widgets[index]) {
            this.setState((prevState) => {
                return {
                    widgets: update(prevState.widgets, {
                        [index]: newData
                    })
                }
            }, () => {
                if (putToServer) {
                    const widget = this.state.widgets[index]
                    const patchData = {
                        x: widget.x,
                        y: widget.y,
                        width: widget.width,
                        height: widget.height,
                    }
                    api.patch('widgets/' + widget.id, patchData).then(() => {
                        // ok
                    }).catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateExam()
                    })
                }
            })
        }
    }

    renderDetails = () => {
        const {
            selectedWidgetIndex,
            widgets,
        } = this.state
        const widget = widgets ? widgets[selectedWidgetIndex] : null

        var isDisabled = true
        var name = ''
        var onNameChange = null
        var onNameSaveClick = null
        if (widget) {
            if (widget.problem) {
                isDisabled = false
                name = widget.problem.name || ''
                onNameChange = (newName) => {
                    this.setState((prevState) => {
                        return {
                            widgets: update(prevState.widgets, {
                                [selectedWidgetIndex]: {
                                    problem: {
                                        name: {
                                            $set: newName
                                        }
                                    }
                                }
                            })
                        }
                    })
                }
                onNameSaveClick = () => {
                    const formData = new FormData()
                    formData.append('name', widget.problem.name)
                    api.put('problems/' + widget.problem.id + '/name', formData).then(() => {
                        // ok
                    }).catch(err => {
                        console.log(err)
                        // update to try and get a consistent state
                        this.updateExam()
                    })
                }
            } else {
                name = widget.name || ''
                onNameChange = () => {
                    // not anyway
                }

            }
        }

        return (
            <nav className="panel">
                <p className="panel-heading">
                    Widget details
                </p>
                <div className="panel-block">
                    <div className="field">
                        <div className="control">
                            <label className="label">Name</label>
                        </div>
                        <div className="control">
                            <input
                                className="input"
                                type="text"
                                disabled={isDisabled}
                                placeholder="Question name"
                                value={name}
                                onChange={(e) => onNameChange(e.target.value)}
                            />
                        </div>
                    </div>
                </div>
                <div className="panel-block">
                    <div className="field">
                        <label className="label">Actions</label>
                    </div>
                </div>
                <div className="panel-block">
                    <div className="field has-addons">
                        <div className="control">
                            <button
                                disabled={isDisabled}
                                className="button is-danger"
                                onClick={() => this.handleWidgetDeletion(selectedWidgetIndex)}
                            >
                                Delete
                            </button>
                        </div>
                        <div className="control">
                            <button
                                disabled={isDisabled}
                                className="button is-success"
                                onClick={() => onNameSaveClick()}
                            >
                                Save name
                            </button>
                        </div>
                    </div>
                </div>
            </nav>
        )
    }

    render = () => {
        const renderedWidgets = this.renderWidgets()
        const details = this.renderDetails()
        return (
            <div className='editor-area columns is-centered' >
                <div className='column is-narrow'  >
                    <div ref={c => this.selectionArea = c} className='selection-area' >
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
                        {renderedWidgets}
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
                            <div className="field-text is-rounded has-text-centered is-link">
                                {'Page ' + (this.state.page + 1) + ' of ' + this.state.numPages}
                            </div>
                        </div>
                        <div className='control'>
                            <button
                                type='submit'
                                className='button is-link is-rounded'
                                onClick={this.nextPage}>Next</button>
                        </div>
                    </div>
                    {details}
                </div>
            </div>
        )
    }
}

PDFEditor.defaultProps = {
    problemMinWidth: 75,
    problemMinHeight: 50,
}

export default PDFEditor

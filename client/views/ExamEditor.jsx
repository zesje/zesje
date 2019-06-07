import React from 'react'

import barcodeExampleImage from '../components/barcode_example.png'
// FIXME!
// eslint-disable-next-line import/no-webpack-loader-syntax
import barcodeExampleImageSize from '!image-dimensions-loader!../components/barcode_example.png'
import studentIdExampleImage from '../components/student_id_example.png'
// FIXME!
// eslint-disable-next-line import/no-webpack-loader-syntax
import studentIdExampleImageSize from '!image-dimensions-loader!../components/student_id_example.png'
import answerBoxImage from '../components/answer_box.png'
import EmptyPDF from '../components/EmptyPDF.jsx'
import PDFOverlay from '../components/PDFOverlay.jsx'

import ResizeAndDrag from 'react-rnd'

import { Document, Page } from 'react-pdf/dist/entry.webpack'

import * as api from '../api.jsx'

class ExamEditor extends React.Component {
  state = {
    mouseDown: false,
    selectionStartPoint: null,
    selectionEndPoint: null,
    selectionBox: null
  }

  getPDFUrl = () => {
    let whichPDF = this.props.finalized ? 'preview' : 'source_pdf'
    return this.props.examID >= 0 ? `/api/exams/${this.props.examID}/${whichPDF}` : null
  }

  getCoordinatesForEvent = (e) => {
    const parentNode = this.selectionArea
    const cumulativeOffset = this.cumulativeOffset(parentNode)
    const scrollY = Math.abs(parentNode.getClientRects()[0].top - cumulativeOffset.top)
    const scrollX = Math.abs(parentNode.getClientRects()[0].left - cumulativeOffset.left)
    return {
      x: e.clientX - cumulativeOffset.left + scrollX,
      y: e.clientY - cumulativeOffset.top + scrollY
    }
  }

  cumulativeOffset = (el) => {
    let top = 0
    let left = 0

    // No tail-call optimization so this is fine
    while (el) {
      top += el.offsetTop || 0
      left += el.offsetLeft || 0
      el = el.offsetParent
    }

    return {
      top: top,
      left: left
    }
  }

  handleMouseDown = (e) => {
    if (e.button === 2 || e.nativeEvent.which === 2) {
      return
    }
    this.props.selectWidget(null)
    this.setState({
      mouseDown: true,
      selectionStartPoint: this.getCoordinatesForEvent(e)
    })

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
          page: this.props.page,
          feedback: [],
          mc_options: [],
          widthMCO: 24,
          heightMCO: 38,
          isMCQ: false
        }
        const widgetData = {
          x: Math.round(selectionBox.left),
          y: Math.round(selectionBox.top),
          width: Math.round(selectionBox.width),
          height: Math.round(selectionBox.height),
          type: 'problem_widget'
        }
        const formData = new window.FormData()
        formData.append('exam_id', this.props.examID)
        formData.append('name', problemData.name)
        formData.append('page', problemData.page)
        formData.append('x', widgetData.x)
        formData.append('y', widgetData.y)
        formData.append('width', widgetData.width)
        formData.append('height', widgetData.height)
        api.post('problems', formData).then(result => {
          widgetData.id = result.widget_id
          problemData.id = result.id
          problemData.name = result.problem_name
          widgetData.problem = problemData

          this.props.createNewWidget(widgetData)
        }).catch(err => {
          console.log(err)
        })
      }
    }
  }

  handleMouseMove = (e) => {
    e.preventDefault()
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
          height >= this.props.problemMinHeight
          ? 'rgba(100, 255, 100, 0.4)'
          : 'rgba(255, 100, 100, 0.4)',
      position: 'absolute',
      zIndex: 99
    }
    return result
  }

  renderSelectionBox = () => {
    if (this.state.mouseDown && this.state.selectionEndPoint && this.state.selectionStartPoint) {
      return (
        <div className='selection-border' style={this.state.selectionBox} />
      )
    } else {
      return null
    }
  }

  /**
   * This method is called when the position of a widget has changed. It informs the server about the relocation.
   * @param widget the widget that was relocated
   * @param data  the new location
   */
  updateWidgetDB = (widget, data) => {
    return api.patch('widgets/' + widget.id, data).then(() => {
      // ok
    }).catch(err => {
      console.log(err)
      // update to try and get a consistent state
      this.props.updateExam()
    })
  }

  /**
   * This function updates the state and the Database with the positions of the mc options.
   * @param widget the problem widget the mc options belong to
   * @param data the new position of the mc widget
   */
  updateMCO = (widget, data) => {
    // update state
    this.props.updateMCWidget(widget, {
      x: Math.round(data.x),
      y: Math.round(data.y)
    })

    // update DB
    widget.problem.mc_options.forEach(
      (option, i) => {
        let newData = {
          x: Math.round(data.x) + i * widget.problem.widthMCO + option.cbOffsetX,
          y: Math.round(data.y) + option.cbOffsetY
        }
        this.updateWidgetDB(option, newData)
      })
  }

  /**
   * This function updates the position of the mc options inside when the corresponding problem widget changes in
   * size or position. Note that the positions in the database are not updated. These should be updated once when the
   * action (resizing/dragging/other) is finalized.
   * @param widget the problem widget containing mc options
   * @param data the new data about the new size/position of the problem widget
   */
  repositionMC = (widget, data) => {
    if (widget.problem.mc_options.length > 0) {
      let oldX = widget.problem.mc_options[0].widget.x
      let oldY = widget.problem.mc_options[0].widget.y
      let newX = oldX
      let newY = oldY
      let widthOption = widget.problem.widthMCO * widget.problem.mc_options.length
      let heightOption = widget.problem.heightMCO
      let widthProblem = data.width ? data.width : widget.width
      let heightProblem = data.height ? data.height : widget.height

      if (newX < data.x) {
        newX = data.x
      } else if (newX + widthOption > data.x + widthProblem) {
        newX = data.x + widget.width - widthOption
      }

      if (newY < data.y) {
        newY = data.y
      } else if (newY + heightOption > data.y + heightProblem) {
        newY = data.y + widget.height - heightOption
      }

      let changed = (oldX !== newX) || (oldY !== newY) // update the state only if the mc options were moved
      if (changed) {
        this.props.updateMCWidget(widget, {
          x: Math.round(newX),
          y: Math.round(newY)
        })
      }
    }
  }

  /**
   * This function renders a group of options into one draggable widget.
   * @param widget the problem widget that contains a mc options
   * @return a react component representing the multiple choice widget
   */
  renderMCWidget = (widget) => {
    let width = widget.problem.widthMCO * widget.problem.mc_options.length
    let height = widget.problem.heightMCO
    let enableResizing = false
    const isSelected = widget.id === this.props.selectedWidgetId
    let xPos = widget.problem.mc_options[0].widget.x
    let yPos = widget.problem.mc_options[0].widget.y

    return (
      <ResizeAndDrag
        key={'widget_mc_' + widget.id}
        bounds={'[data-key="widget_' + widget.id + '"]'}
        minWidth={width}
        minHeight={height}
        enableResizing={{
          bottom: enableResizing,
          bottomLeft: enableResizing,
          bottomRight: enableResizing,
          left: enableResizing,
          right: enableResizing,
          top: enableResizing,
          topLeft: enableResizing,
          topRight: enableResizing
        }}
        position={{
          x: xPos,
          y: yPos
        }}
        size={{
          width: width,
          height: height
        }}
        onDragStart={() => {
          this.props.selectWidget(widget.id)
        }}
        onDragStop={(e, data) => {
          this.updateMCO(widget, data)
        }}
      >
        <div className={isSelected ? 'mcq-widget widget selected' : 'mcq-widget widget '}>
          {widget.problem.mc_options.map((option) => {
            return (
              <div key={'widget_mco_' + option.id} className='mcq-option'>
                <div className='mcq-option-label'>
                  {option.label}
                </div>
                <img className='mcq-box' src={answerBoxImage} />
              </div>
            )
          })}
        </div>
      </ResizeAndDrag>
    )
  }

  /**
   * Render problem widget and the mc options that correspond to the problem.
   * @param widget the corresponding widget object from the db
   * @returns {Array} an array of react components to be displayed
   */
  renderProblemWidget = (widget) => {
    // Only render when numPage is set
    if (widget.problem.page !== this.props.page) return []

    let enableResizing = true
    const isSelected = widget.id === this.props.selectedWidgetId
    let minWidth = this.props.problemMinWidth
    let minHeight = this.props.problemMinHeight
    let elementList = [(
      <ResizeAndDrag
        key={'widget_' + widget.id}
        data-key={'widget_' + widget.id}
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
          topRight: enableResizing
        }}
        position={{
          x: widget.x,
          y: widget.y
        }}
        size={{
          width: widget.width,
          height: widget.height
        }}
        onResize={(e, direction, ref, delta, position) => {
          this.props.updateWidget(widget.id, {
            width: { $set: ref.offsetWidth },
            height: { $set: ref.offsetHeight },
            x: { $set: Math.round(position.x) },
            y: { $set: Math.round(position.y) }
          })
          this.repositionMC(widget, {
            width: ref.offsetWidth,
            height: ref.offsetHeight,
            x: Math.round(position.x),
            y: Math.round(position.y)
          })
        }}
        onResizeStop={(e, direction, ref, delta, position) => {
          this.updateWidgetDB(widget, {
            x: Math.round(position.x),
            y: Math.round(position.y),
            width: ref.offsetWidth,
            height: ref.offsetHeight
          }).then(() => {
            if (widget.problem.mc_options.length > 0) {
              this.updateMCO(widget, {
                x: widget.problem.mc_options[0].widget.x, // these are guaranteed to be up to date
                y: widget.problem.mc_options[0].widget.y
              })
            }
          })
        }}
        onDragStart={() => {
          this.props.selectWidget(widget.id)
        }}
        onDrag={(e, data) => this.repositionMC(widget, data)}
        onDragStop={(e, data) => {
          this.props.updateWidget(widget.id, {
            x: { $set: Math.round(data.x) },
            y: { $set: Math.round(data.y) }
          })
          this.updateWidgetDB(widget, {
            x: Math.round(data.x),
            y: Math.round(data.y)
          }).then(() => {
            if (widget.problem.mc_options.length > 0) {
              this.updateMCO(widget, {
                // react offers the guarantee that setState calls are processed before handling next event
                // therefore the data in the state is up to date
                x: widget.problem.mc_options[0].widget.x,
                y: widget.problem.mc_options[0].widget.y
              })
            }
          })
        }}
      >
        <div
          className={isSelected ? 'widget selected' : 'widget'}
        />
      </ResizeAndDrag>
    )]

    // depending on the rendering option, render the mc_options separately or in a single widget
    if (widget.problem.mc_options.length > 0 && !this.props.finalized) {
      elementList.push(this.renderMCWidget(widget))
    }

    return elementList
  }

  /**
   * Render exam widgets.
   * @param widget the corresponding widget object from the db
   * @returns {Array} an array of react components to be displayed
   */
  renderExamWidget = (widget) => {
    if (this.props.finalized) return []

    let minWidth, minHeight
    let enableResizing = false
    const isSelected = widget.id === this.props.selectedWidgetId
    let image
    if (widget.name === 'barcode_widget') {
      minWidth = barcodeExampleImageSize.width
      minHeight = barcodeExampleImageSize.height
      image = barcodeExampleImage
    } else if (this.props.page === 0 && widget.name === 'student_id_widget') {
      minWidth = studentIdExampleImageSize.width
      minHeight = studentIdExampleImageSize.height
      image = studentIdExampleImage
    } else {
      return []
    }

    return [(
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
          topRight: enableResizing
        }}
        position={{
          x: widget.x,
          y: widget.y
        }}
        size={{
          width: widget.width,
          height: widget.height
        }}
        onDragStart={() => {
          this.props.selectWidget(widget.id)
        }}
        onDragStop={(e, data) => {
          this.props.updateWidget(widget.id, {
            x: { $set: Math.round(data.x) },
            y: { $set: Math.round(data.y) }
          })
          this.updateWidgetDB(widget, {
            x: Math.round(data.x),
            y: Math.round(data.y)
          })
        }}
      >
        <div
          className={isSelected ? 'widget selected' : 'widget'}
          style={{
            boxSizing: 'content-box',
            backgroundImage: 'url(' + image + ')',
            backgroundRepeat: 'no-repeat'
          }}
        />
      </ResizeAndDrag>
    )]
  }

  /**
   * Render all the widgets by calling the right rendering function for each widget type
   * @returns {Array} containing all widgets components to be displayed
   */
  renderWidgets = () => {
    // Only render when numPage is set
    if (this.props.numPages !== null && this.props.widgets) {
      let widgets = this.props.widgets
      let elementList = []

      widgets.forEach((widget) => {
        if (widget.type === 'exam_widget') {
          elementList = elementList.concat(this.renderExamWidget(widget))
        } else if (widget.type === 'problem_widget') {
          elementList = elementList.concat(this.renderProblemWidget(widget))
        }
      })

      return elementList
    }
  }

  render = () => {
    return (
      <div
        ref={c => (this.selectionArea = c)}
        className='selection-area'
      >
        <Document
          file={this.getPDFUrl()}
          onLoadSuccess={this.props.onPDFLoad}
          loading={<EmptyPDF />}
          noData={<EmptyPDF />}
        >
          <Page
            renderAnnotations={false}
            renderTextLayer={false}
            pageIndex={this.props.page}
            onMouseDown={this.handleMouseDown} />
        </Document>
        <PDFOverlay />
        {this.renderWidgets()}
        {this.renderSelectionBox()}
      </div>
    )
  }
}

ExamEditor.defaultProps = {
  problemMinWidth: 75,
  problemMinHeight: 50
}

export default ExamEditor

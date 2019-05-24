import React from 'react'

import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'
import './Exam.css'
import GeneratedExamPreview from '../components/GeneratedExamPreview.jsx'
import PanelGenerate from '../components/PanelGenerate.jsx'
import PanelMCQ from '../components/PaneMCQ.jsx'
import ExamEditor from './ExamEditor.jsx'
import update from 'immutability-helper'
import ExamFinalizeMarkdown from './ExamFinalize.md'
import ConfirmationModal from '../components/ConfirmationModal.jsx'

import * as api from '../api.jsx'

class Exams extends React.Component {
  state = {
    examID: null,
    page: 0,
    numPages: null,
    selectedWidgetId: null,
    changedWidgetId: null,
    widgets: [],
    previewing: false,
    deletingExam: false,
    deletingWidget: false,
    deletingMCWidget: false,
    showPanelMCQ: false
  }

  static getDerivedStateFromProps = (newProps, prevState) => {
    if (newProps.exam.id !== prevState.examID) {
      // initialize array to size of pdf
      const widgets = []
      newProps.exam.problems.forEach(problem => {
        // keep page and name of problem as widget.problem object
        widgets[problem.widget.id] = {
          ...problem.widget,
          problem: {
            id: problem.id,
            page: problem.page,
            name: problem.name,
            graded: problem.graded,
            mc_options: problem.mc_options.map((option) => {
              option.cbOffsetX = 7 // checkbox offset relative to option position on x axis
              option.cbOffsetY = 21 // checkbox offset relative to option position on y axis
              option.widget.x -= option.cbOffsetX
              option.widget.y -= option.cbOffsetY
              return option
            }),
            widthMCO: 24,
            heightMCO: 38,
            isMCQ: problem.mc_options && problem.mc_options.length !== 0 // is the problem a mc question - used to display PanelMCQ
          }
        }
      })

      newProps.exam.widgets.forEach(examWidget => {
        widgets[examWidget.id] = examWidget
      })

      return {
        examID: newProps.exam.id,
        page: 0,
        numPages: null,
        selectedWidgetId: null,
        changedWidgetId: null,
        widgets: widgets,
        previewing: false
      }
    }

    return null
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID) {
      this.props.updateExam(this.props.examID)
    }
    // This saves the problem name when switching to non-problem widgets
    // The onBlur event is not fired when the input field is being disabled
    if (prevState.selectedWidgetId !== this.state.selectedWidgetId) {
      this.saveProblemName()
    }
  }

  componentDidMount = () => {
    if (this.props.examID !== this.props.exam.id) this.props.updateExam(this.props.examID)
  }

  componentWillUnmount = () => {
    // This might try to save the name unnecessary, but better twice than never.
    this.saveProblemName()
    // Force an update of the upper exam state, since this component does not update and use that correctly
    this.props.updateExam(this.props.examID)
  }

  saveProblemName = () => {
    const changedWidgetId = this.state.changedWidgetId
    if (!changedWidgetId) return

    const changedWidget = this.state.widgets[changedWidgetId]
    if (!changedWidget) return

    const problem = changedWidget.problem
    if (!problem) return

    api.put('problems/' + problem.id + '/name', { name: problem.name })
      .catch(e => Notification.error('Could not save new problem name: ' + e))
      .then(this.setState({
        changedWidgetId: null
      }))
  }

  createNewWidget = (widgetData) => {
    this.setState((prevState) => {
      return {
        selectedWidgetId: widgetData.id,
        widgets: update(prevState.widgets, {
          [widgetData.id]: {
            $set: widgetData
          }
        })
      }
    })
  }

  deleteWidget = (widgetId) => {
    const widget = this.state.widgets[widgetId]
    if (widget) {
      api.del('problems/' + widget.problem.id)
        .then(() => {
          this.setState((prevState) => {
            return {
              selectedWidgetId: null,
              changedWidgetId: null,
              deletingWidget: false,
              widgets: update(prevState.widgets, {
                $unset: [widgetId]
              })
            }
          })
        })
        .catch(err => {
          console.log(err)
          err.json().then(res => {
            this.setState({
              deletingWidget: false
            })
            Notification.error('Could not delete problem' +
              (res.message ? ': ' + res.message : ''))
            // update to try and get a consistent state
            this.props.updateExam(this.props.examID)
          })
        })
    }
  }

  updateWidget = (widgetId, newData) => {
    this.setState(prevState => ({
      widgets: update(prevState.widgets, {
        [widgetId]: newData
      })
    }))
  }

  renderContent = () => {
    if (this.state.previewing) {
      return (
        <GeneratedExamPreview
          examID={this.state.examID}
          page={this.state.page}
          onPDFLoad={this.onPDFLoad}
        />
      )
    } else {
      return (
        <ExamEditor
          finalized={this.props.exam.finalized}
          widgets={this.state.widgets}
          examID={this.state.examID}
          page={this.state.page}
          numPages={this.state.numPages}
          onPDFLoad={this.onPDFLoad}
          updateWidget={this.updateWidget}
          selectedWidgetId={this.state.selectedWidgetId}
          selectWidget={(widgetId) => {
            this.setState({
              selectedWidgetId: widgetId
            })
          }}
          createNewWidget={this.createNewWidget}
          updateMCWidgetPosition={this.updateMCWidgetPosition}
          updateExam={() => {
            this.props.updateExam(this.props.examID)
          }}
        />
      )
    }
  }

  Pager = (props) => {
    const isDisabled = props.numPages == null
    const pageNum = isDisabled ? '_' : props.page + 1
    const numPages = isDisabled ? '_' : props.numPages
    return (
      <div className='field has-addons is-mobile'>
        <div className='control'>
          <button
            disabled={isDisabled}
            type='submit'
            className='button is-link is-rounded'
            onClick={() => props.setPage(props.page - 1)}
          >
            Previous
          </button>
        </div>
        <div className='control'>
          <div className='field-text is-rounded has-text-centered is-link'>
            {'Page ' + pageNum + ' of ' + numPages}
          </div>
        </div>
        <div className='control'>
          <button
            disabled={isDisabled}
            type='submit'
            className='button is-link is-rounded'
            onClick={() => props.setPage(props.page + 1)}
          >
            Next
          </button>
        </div>
      </div>
    )
  }

  onPDFLoad = (pdf) => {
    this.setState((newProps, prevState) => ({
      numPages: pdf.numPages
    }), () => {
      this.props.updateExam(this.props.examID)
    })
  }

  setPage = (newPage) => {
    this.setState((prevState) => {
      return {
        // clamp the page
        selectedWidgetId: null,
        page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
      }
    })
  }

  /**
   * This function deletes the mc options coupled to a problem.
   */
  deleteMCWidget = () => {
    const widget = this.state.widgets[this.state.selectedWidgetId]
    const options = widget.problem.mc_options
    if (options.length > 0) {
      options.forEach((option) => {
        api.del('mult-choice/' + option.id)
          .catch(err => {
            console.log(err)
            err.json().then(res => {
              this.setState({
                deletingMCWidget: false
              })
              Notification.error('Could not delete multiple choice option' +
                (res.message ? ': ' + res.message : ''))
              // update to try and get a consistent state
              this.props.updateExam(this.props.examID)
            })
          })
      })

      // remove the mc options from the state
      // note that his can happen before they are removed in the DB due to async calls
      this.setState((prevState) => {
        return {
          widgets: update(prevState.widgets, {
            [widget.id]: {
              problem: {
                mc_options: {
                  $set: []
                }
              }
            }
          }),
          deletingMCWidget: false
        }
      })
    }
  }

  /**
   * This method creates a mc option widget object and adds it to the corresponding problem
   * @param problemWidget The widget the mc option belongs to
   * @param data the mc option
   */
  createNewMCOWidget = (problemWidget, data) => {
    this.setState((prevState) => {
      return {
        widgets: update(prevState.widgets, {
          [this.state.selectedWidgetId]: {
            problem: {
              mc_options: {
                $push: [data]
              }
            }
          }
        })
      }
    })
  }

  /**
   * This method is called when the mcq widget is moved. The positions of the options are stored separately and they
  * all need to be updated
   * @param widget the problem widget that includes the mcq widget
   * @param data the new location of the mcq widget (the location of the top-left corner)
   */
  updateMCWidgetPosition = (widget, data) => {
    let newMCO = widget.problem.mc_options.map((option, i) => {
      return {
        'widget': {
          'x': {
            $set: data.x + i * widget.problem.widthMCO
          },
          'y': {
            // each mc option needs to be positioned next to the previous option and should not overlap it
            $set: data.y
          }
        }
      }
    })

    // update the state with the new locations
    this.setState(prevState => ({
      widgets: update(prevState.widgets, {
        [widget.id]: {
          'problem': {
            'mc_options': newMCO
          }
        }
      })
    }))
  }

  /**
   * This method generates MC options by making the right calls to the api and creating
   * the widget object in the mc_options array of the corresponding problem.
   * @param problemWidget the problem widget the mc options belong to
   * @param labels the labels for the options
   * @param index the index in the labels array (the function is recusive, this index is increased)
   * @param xPos x position of the current option
   * @param yPos y position of the current option
   */
  generateAnswerBoxes = (problemWidget, labels, index, xPos, yPos) => {
    if (labels.length === index) return

    let data = {
      'label': labels[index],
      'problem_id': problemWidget.problem.id,
      'feedback_id': null,
      'cbOffsetX': 7, // checkbox offset relative to option position on x axis
      'cbOffsetY': 21, // checkbox offset relative to option position on y axis
      'widget': {
        'name': 'mc_option_' + labels[index],
        'x': xPos,
        'y': yPos,
        'type': 'mcq_widget'
      }
    }

    const formData = new window.FormData()
    formData.append('name', data.widget.name)
    formData.append('x', data.widget.x + data.cbOffsetX)
    formData.append('y', data.widget.y + data.cbOffsetY)
    formData.append('problem_id', data.problem_id)
    formData.append('label', data.label)
    api.put('mult-choice/', formData).then(result => {
      data.id = result.mult_choice_id
      this.createNewMCOWidget(problemWidget, data)
      this.generateAnswerBoxes(problemWidget, labels, index + 1, xPos + problemWidget.problem.widthMCO, yPos)
    }).catch(err => {
      console.log(err)
    })
  }

  SidePanel = (props) => {
    const selectedWidgetId = this.state.selectedWidgetId
    let selectedWidget = selectedWidgetId && this.state.widgets[selectedWidgetId]
    let problem = selectedWidget && selectedWidget.problem
    let widgetEditDisabled = this.state.previewing || !problem
    let isGraded = problem && problem.graded
    let widgetDeleteDisabled = widgetEditDisabled || isGraded
    let totalNrAnswers = 12 // the upper limit for the nr of possible answer boxes
    let containsMCOptions = (problem && problem.mc_options.length > 0) || false
    let disabledDeleteBoxes = !containsMCOptions
    let isMCQ = (problem && problem.isMCQ) || false

    return (
      <React.Fragment>
        <this.PanelEdit
          disabledEdit={widgetEditDisabled}
          disableIsMCQ={widgetEditDisabled || containsMCOptions}
          disabledDelete={widgetDeleteDisabled}
          onDeleteClick={() => {
            this.setState({deletingWidget: true})
          }}
          problem={problem}
          changeProblemName={newName => {
            this.setState(prevState => ({
              changedWidgetId: selectedWidgetId,
              widgets: update(prevState.widgets, {
                [selectedWidgetId]: {
                  problem: {
                    name: {
                      $set: newName
                    }
                  }
                }
              })
            }))
          }}
          saveProblemName={this.saveProblemName}
          isMCQProblem={isMCQ}
          onMCQChange={
            (checked) => {
              this.setState(prevState => ({
                changedWidgetId: selectedWidgetId,
                widgets: update(prevState.widgets, {
                  [selectedWidgetId]: {
                    problem: {
                      isMCQ: {
                        $set: checked
                      }
                    }
                  }
                })
              }))
            }
          }
        />
        { isMCQ ? (
          <PanelMCQ
            totalNrAnswers={totalNrAnswers}
            disabledGenerateBoxes={containsMCOptions}
            disabledDeleteBoxes={disabledDeleteBoxes}
            problem={problem}
            onGenerateBoxesClick={(labels) => {
              let problemWidget = this.state.widgets[this.state.selectedWidgetId]
              // position the new mc option widget inside the problem widget
              let xPos = problemWidget.x + 2
              let yPos = problemWidget.y + 2
              this.generateAnswerBoxes(problemWidget, labels, 0, xPos, yPos)
            }}
            onDeleteBoxesClick={() => {
              this.setState({deletingMCWidget: true})
            }}
          />
        ) : null }
        <this.PanelExamActions />
      </React.Fragment>
    )
  }

  PanelEdit = (props) => {
    const selectedWidgetId = this.state.selectedWidgetId

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Problem details
        </p>
        {selectedWidgetId === null ? (
          <div className='panel-block'>
            <div className='field'>
              <p style={{ margin: '0.625em 0', minHeight: '3em' }}>
                To create a problem, draw a rectangle on the exam.
              </p>
            </div>
          </div>
        ) : (
          <React.Fragment>
            <div className='panel-block'>
              <div className='field'>
                <label className='label'>Name</label>
                <div className='control'>
                  <input
                    disabled={props.disabledEdit}
                    className='input'
                    placeholder='Problem name'
                    value={props.problem ? props.problem.name : ''}
                    onChange={(e) => {
                      props.changeProblemName(e.target.value)
                    }}
                    onBlur={(e) => {
                      props.saveProblemName(e.target.value)
                    }}
                  />
                </div>
              </div>
            </div>
            <div className='panel-block'>
              <div className='field'>
                <label className='label'>
                  <input disabled={props.disableIsMCQ} type='checkbox' checked={props.isMCQProblem} onChange={
                    (e) => {
                      props.onMCQChange(e.target.checked)
                    }} />
                    Multiple choice question
                </label>
              </div>
            </div>
          </React.Fragment>
        )}
        <div className='panel-block'>
          <button
            disabled={props.disabledDelete}
            className='button is-danger is-fullwidth'
            onClick={() => props.onDeleteClick()}
          >
            Delete problem
          </button>
        </div>
      </nav>
    )
  }

  PanelExamActions = () => {
    if (this.props.exam.finalized) {
      return <PanelGenerate examID={this.state.examID} />
    }

    let actionsBody
    if (this.state.previewing) {
      actionsBody =
        <this.PanelConfirm
          onYesClick={() =>
            api.put(`exams/${this.props.examID}/finalized`, 'true')
              .then(() => {
                this.props.updateExam(this.props.examID)
                this.setState({ previewing: false })
              })
          }
          onNoClick={() => this.setState({
            previewing: false
          })}
        />
    } else {
      actionsBody =
        <div className='panel-block field is-grouped'>
          <this.Finalize />
          <this.Delete />
        </div>
    }

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Actions
        </p>
        {actionsBody}
      </nav>
    )
  }

  Finalize = (props) => {
    return (
      <button
        className='button is-link is-fullwidth'
        onClick={() => { this.setState({previewing: true}) }}
      >
        Finalize
      </button>
    )
  }

  Delete = (props) => {
    return (
      <button
        className='button is-link is-fullwidth is-danger'
        onClick={() => { this.setState({deletingExam: true}) }}
      >
        Delete exam
      </button>
    )
  }

  PanelConfirm = (props) => {
    return (
      <div>
        <div className='panel-block'>
          <label className='label'>Are you sure?</label>
        </div>
        <div className='content panel-block' dangerouslySetInnerHTML={{__html: ExamFinalizeMarkdown}} />
        <div className='panel-block field is-grouped'>
          <button
            disabled={props.disabled}
            className='button is-danger is-link is-fullwidth'
            onClick={() => props.onYesClick()}
          >
            Yes
          </button>
          <button
            disabled={props.disabled}
            className='button is-link is-fullwidth'
            onClick={() => props.onNoClick()}
          >
            No
          </button>
        </div>
      </div>
    )
  }

  render () {
    return <div>
      <Hero />
      <section className='section'>
        <div className='container'>
          <div className='columns is-centered' >
            <div className='column is-one-quarter-widescreen is-one-third-desktop editor-side-panel' >
              <p className='title is-1'>Exam details</p>
              <p className='subtitle is-3'>{'Selected: ' + this.props.exam.name}</p>
              <this.Pager
                page={this.state.page}
                numPages={this.state.numPages}
                setPage={this.setPage}
              />
              <this.SidePanel examID={this.state.examID} />
            </div>
            <div className='column is-narrow editor-content' >
              {this.renderContent()}
            </div>
          </div>
        </div>
      </section>
      <ConfirmationModal
        active={this.state.deletingExam}
        color='is-danger'
        headerText={`Are you sure you want to delete exam "${this.props.exam.name}"?`}
        confirmText='Delete exam'
        onCancel={() => this.setState({deletingExam: false})}
        onConfirm={() => {
          this.props.deleteExam(this.props.examID).then(this.props.leave)
        }}
      />
      <ConfirmationModal
        active={this.state.deletingWidget && this.state.selectedWidgetId != null}
        color='is-danger'
        headerText={`Are you sure you want to delete problem "${
          this.state.selectedWidgetId &&
          this.state.widgets[this.state.selectedWidgetId] &&
          this.state.widgets[this.state.selectedWidgetId].problem &&
          this.state.widgets[this.state.selectedWidgetId].problem.name}"`}
        confirmText='Delete problem'
        onCancel={() => this.setState({deletingWidget: false})}
        onConfirm={() => this.deleteWidget(this.state.selectedWidgetId)}
      />
      <ConfirmationModal
        active={this.state.deletingMCWidget && this.state.selectedWidgetId != null}
        color='is-danger'
        headerText={`Are you sure you want to delete the multiple choice options for problem "${
          this.state.selectedWidgetId &&
          this.state.widgets[this.state.selectedWidgetId] &&
          this.state.widgets[this.state.selectedWidgetId].problem &&
          this.state.widgets[this.state.selectedWidgetId].problem.name}"`}
        confirmText='Delete multiple choice options'
        onCancel={() => this.setState({deletingMCWidget: false})}
        onConfirm={() => this.deleteMCWidget(this.state.selectedWidgetId)}
      />
    </div>
  }
}

export default Exams

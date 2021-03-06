import React from 'react'

import Notification from 'react-bulma-notification'
import update from 'immutability-helper'

import GeneratedExamPreview from '../../components/GeneratedExamPreview.jsx'
import PanelGenerate from '../../components/PanelGenerate.jsx'
import PanelMCQ from '../../components/PanelMCQ.jsx'
import ConfirmationModal from '../../components/ConfirmationModal.jsx'
import FeedbackPanel from '../../components/feedback/FeedbackPanel.jsx'
import Tooltip from '../../components/Tooltip.jsx'

import ExamEditor from './ExamEditor.jsx'
import PanelGradeAnonymous from './PanelGradeAnonymous.jsx'
import ExamFinalizeMarkdown from './ExamFinalize.md'
import PanelExamName from './PanelExamName.jsx'
import PanelFinalize from './PanelFinalize.jsx'

import './Exam.css'

import * as api from '../../api.jsx'

const Pager = (props) => {
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
      <div className='control is-expanded'>
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

class ExamTemplated extends React.Component {
  state = {
    examID: null,
    page: 0,
    editActive: false,
    feedbackToEdit: null,
    problemIdToEditFeedbackOf: null,
    numPages: null,
    selectedWidgetId: null,
    changedWidgetId: null,
    widgets: {},
    previewing: false,
    deletingWidget: false,
    deletingMCWidget: false,
    showPanelMCQ: false
  }

  static getDerivedStateFromProps = (newProps, prevState) => {
    if (newProps.exam.id !== prevState.examID) {
      // initialize array to size of pdf
      const widgets = {}
      newProps.exam.problems.forEach(problem => {
        // keep page and name of problem as widget.problem object
        widgets[problem.widget.id] = {
          ...problem.widget,
          problem: {
            id: problem.id,
            page: problem.page,
            name: problem.name,
            n_graded: problem.n_graded,
            grading_policy: problem.grading_policy,
            feedback: problem.feedback || [],
            mc_options: problem.mc_options.map((option) => {
              // the database stores the positions of the checkboxes but the front end uses the top-left position
              // of the option; the cbOffsetX and cbOffsetY are used to manually locate the checkbox precisely
              option.cbOffsetX = 7 // checkbox offset relative to option position on x axis
              option.cbOffsetY = 21 // checkbox offset relative to option position on y axis
              option.widget.x -= option.cbOffsetX
              option.widget.y -= option.cbOffsetY
              return option
            }),
            widthMCO: 20,
            heightMCO: 34
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
    // This saves the problem name when switching to non-problem widgets
    // The onBlur event is not fired when the input field is being disabled
    if (prevState.selectedWidgetId !== this.state.selectedWidgetId) {
      this.saveProblemName()
      this.setState({
        editActive: false,
        problemIdToEditFeedbackOf: false
      })
    }
  }

  componentWillUnmount = () => {
    // This might try to save the name unnecessary, but better twice than never.
    this.saveProblemName()
  }

  editFeedback = (feedback) => {
    this.setState({
      editActive: true,
      feedbackToEdit: feedback,
      problemIdToEditFeedbackOf: this.state.selectedWidgetId
    })
  }

  updateFeedback = (problemId) => {
    const problemWidget = Object.values(this.state.widgets).find(widget => widget.problem && widget.problem.id === problemId)
    const problemWidgetId = problemWidget.id
    api.get(`problems/${problemId}`).then(problem => {
      this.setState((prevState) => ({
        widgets: {
          ...prevState.widgets,
          [problemWidgetId]: {
            ...prevState.widgets[problemWidgetId],
            problem: {
              ...prevState.widgets[problemWidgetId].problem,
              feedback: problem.feedback
            }
          }
        }
      }))
    })
  }

  /**
   * Update feedback corresponding to a problem
   * @param feedback the feedback to be created/deleted/updated
   * @param problemWidget the problem that contains the feedback
   * @param idx the location of the feedback in the feedback field of the problem
   */
  updateFeedbackAtIndex = (feedback, problemWidget, idx) => {
    if (idx === -1) {
      // in case the feedback doesn't exist, create a new feedback object
      this.setState((prevState) => {
        return {
          widgets: update(prevState.widgets, {
            [problemWidget.id]: {
              'problem': {
                'feedback': {
                  $push: [feedback]
                }
              }
            }
          })
        }
      })
    } else if (feedback.deleted) {
      // delete the feedback if the deleted field is set
      this.setState((prevState) => {
        return {
          widgets: update(prevState.widgets, {
            [problemWidget.id]: {
              'problem': {
                'feedback': {
                  $splice: [[idx, 1]]
                }
              }
            }
          })
        }
      })
    } else {
      // update the existing feedback
      this.setState(prevState => {
        return {
          widgets: update(prevState.widgets, {
            [problemWidget.id]: {
              'problem': {
                'feedback': {
                  [idx]: {
                    $set: feedback
                  }
                }
              }
            }
          })
        }
      })
    }
  }

  backToFeedback = () => {
    this.props.updateExam()
    this.setState({
      editActive: false
    })
  }

  saveProblemName = () => {
    const changedWidgetId = this.state.changedWidgetId
    if (!changedWidgetId) return

    const changedWidget = this.state.widgets[changedWidgetId]
    if (!changedWidget) return

    const problem = changedWidget.problem
    if (!problem) return

    api.put('problems/' + problem.id, { name: problem.name })
      .catch(e => Notification.error('Could not save new problem name: ' + e))
      .then(this.setState({
        changedWidgetId: null
      }))
  }

  onChangeAutoApproveType (e) {
    const selectedWidgetId = this.state.selectedWidgetId
    if (!selectedWidgetId) return

    const selectedWidget = this.state.widgets[selectedWidgetId]
    if (!selectedWidget) return

    const problem = selectedWidget.problem
    if (!problem) return

    const newPolicy = e.target.value

    api.put('problems/' + problem.id, { grading_policy: newPolicy })
      .then(success => this.setState(prevState => ({
        widgets: update(prevState.widgets, {
          [selectedWidgetId]: {
            problem: {
              grading_policy: {
                $set: newPolicy
              }
            }
          }
        })
      })), error => {
        error.json().then(res => {
          let message = res.message
          if (typeof message === 'object') {
            message = Object.values(message)[0]
          }
          Notification.error('Could not change grading policy: ' + message)
        })
      })
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
              editActive: false,
              problemIdToEditFeedbackOf: null,
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
            this.props.updateExam()
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
          updateMCOsInState={this.updateMCOsInState}
          selectedWidgetId={this.state.selectedWidgetId}
          highlightFeedback={(widget, feedbackId) => {
            let index = widget.problem.feedback.findIndex(e => { return e.id === feedbackId })
            let feedback = widget.problem.feedback[index]
            feedback.highlight = true
            this.updateFeedbackAtIndex(feedback, widget, index)
          }}
          removeHighlight={(widget, feedbackId) => {
            let index = widget.problem.feedback.findIndex(e => { return e.id === feedbackId })
            let feedback = widget.problem.feedback[index]
            feedback.highlight = false
            this.updateFeedbackAtIndex(feedback, widget, index)
          }}
          removeAllHighlight={(widget) => {
            widget.problem.feedback.forEach((feedback, index) => {
              feedback.highlight = false
              this.updateFeedbackAtIndex(feedback, widget, index)
            })
          }}
          selectWidget={(widgetId) => {
            this.setState({
              selectedWidgetId: widgetId
            })
          }}
          createNewWidget={this.createNewWidget}
          updateExam={this.props.updateExam}
        />
      )
    }
  }

  onPDFLoad = (pdf) => {
    this.setState((newProps, prevState) => ({
      numPages: pdf.numPages
    }), () => {
      this.props.updateExam()
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
   * This method generates MC options by making the right calls to the api and creating
   * the widget object in the mc_options array of the corresponding problem.
   * @param problemWidget the problem widget the mc options belong to
   * @param labels the labels for the options
   * @param index the index in the labels array (the function is recusive, this index is increased)
   * @param xPos x position of the current option
   * @param yPos y position of the current option
   */
  generateMCOs = (problemWidget, labels, index, xPos, yPos) => {
    if (labels.length === index) {
      return true
    }

    let feedback = {
      'name': labels[index],
      'description': '',
      'score': 0
    }

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
    return api.put('mult-choice/', formData).then(result => {
      data.id = result.mult_choice_id
      data.feedback_id = result.feedback_id
      feedback.id = result.feedback_id
      this.addMCOtoState(problemWidget, data)
      this.updateFeedback(problemWidget.problem.id)
      return this.generateMCOs(problemWidget, labels, index + 1, xPos + problemWidget.problem.widthMCO, yPos)
    }).catch(err => {
      console.log(err)
      err.json().then(res => {
        Notification.error('Could not create multiple choice option' +
          (res.message ? ': ' + res.message : ''))
        // update to try and get a consistent state
        this.props.updateExam()
        this.setState({
          selectedWidgetId: null
        })
        return false
      })
    })
  }

  /**
   * This method creates a mc option widget object and adds it to the corresponding problem in the state
   * @param problemWidget The widget the mc option belongs to
   * @param data the mc option
   */
  addMCOtoState = (problemWidget, data) => {
    this.setState((prevState) => {
      return {
        widgets: update(prevState.widgets, {
          [problemWidget.id]: {
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
   * This method deletes mc options coupled to a problem in both the state and the database.
   * @param widgetId the id of the widget for which the mc options need to be deleted
   * @param index the index of the first mc option to be removed
   * @param nrMCOs the number of mc options to remove
   * @returns {Promise<boolean>} a promise that contains true if the operation was successful and false otherwise
   */
  deleteMCOs = (widgetId, index, nrMCOs) => {
    let widget = this.state.widgets[widgetId]
    if (nrMCOs <= 0 || !widget.problem.mc_options.length) return Promise.resolve(true)

    let option = widget.problem.mc_options[index]
    if (!option) return Promise.resolve(false)

    return api.del('mult-choice/' + option.id)
      .then(res => {
        let indexFb = widget.problem.feedback.findIndex(e => { return e.id === option.feedback_id })
        let feedback = widget.problem.feedback[indexFb]
        feedback.deleted = true
        this.updateFeedbackAtIndex(feedback, widget, indexFb)
        return new Promise((resolve) => {
          this.setState((prevState) => {
            return {
              widgets: update(prevState.widgets, {
                [widget.id]: {
                  problem: {
                    mc_options: {
                      $splice: [[index, 1]]
                    }
                  }
                }
              })
            }
          }, () => {
            resolve(this.deleteMCOs(widgetId, index, nrMCOs - 1))
          })
        })
      })
      .catch(err => {
        console.log(err)
        err.json().then(res => {
          Notification.error('Could not delete multiple choice option' +
            (res.message ? ': ' + res.message : ''))
          // update to try and get a consistent state
          this.props.updateExam()
          this.setState({
            selectedWidgetId: null
          })
          return Promise.resolve(false)
        })
      })
  }

  /**
   * This method is called when the mcq widget is moved. The positions of the options are stored separately and they
  * all need to be updated in the state. This method does not update the positions of the mc options in the DB.
   * @param widget the problem widget that includes the mcq widget
   * @param data the new location of the mcq widget (the location of the top-left corner)
   */
  updateMCOsInState = (widget, data) => {
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

  SidePanel = (props) => {
    const selectedWidgetId = this.state.selectedWidgetId
    let selectedWidget = selectedWidgetId && this.state.widgets[selectedWidgetId]
    let problem = selectedWidget && selectedWidget.problem
    let widgetEditDisabled = (this.state.previewing || !problem)
    let isGraded = problem && problem.n_graded > 0
    let widgetDeleteDisabled = widgetEditDisabled || isGraded

    return (
      <React.Fragment>
        <Pager
          page={this.state.page}
          numPages={this.state.numPages}
          setPage={this.setPage}
        />
        <this.PanelEdit
          disabledEdit={widgetEditDisabled}
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
          setHelpPage={this.props.setHelpPage}
        />
        <this.PanelExamActions />
        {this.props.exam.finalized && <PanelGradeAnonymous
          examID={this.props.exam.id}
          gradeAnonymous={this.props.exam.gradeAnonymous}
          onChange={(anonymous) => this.props.updateExam()} />}
      </React.Fragment>
    )
  }

  PanelEdit = (props) => {
    const selectedWidgetId = this.state.selectedWidgetId
    let totalNrAnswers = 9 // the upper limit for the nr of possible answer boxes

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Problem details
        </p>
        {selectedWidgetId === null || !props.problem ? (
          <div className='panel-block'>
            <div className='field'>
              <p>
                To create a problem, draw a rectangle on the exam.
              </p>
            </div>
          </div>
        ) : (
          <React.Fragment>
            <div className='panel-block'>
              <div className='field' style={{flexGrow: 1}}>
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
            {props.problem && !this.props.exam.finalized ? (
              <PanelMCQ
                totalNrAnswers={totalNrAnswers}
                problem={props.problem}
                generateMCOs={(labels) => {
                  let problemWidget = this.state.widgets[this.state.selectedWidgetId]
                  let xPos, yPos
                  if (props.problem.mc_options.length > 0) {
                    // position the new mc options widget next to the last mc options
                    let last = props.problem.mc_options[props.problem.mc_options.length - 1].widget
                    xPos = last.x + problemWidget.problem.widthMCO
                    yPos = last.y
                  } else {
                    // position the new mc option widget inside the problem widget
                    xPos = problemWidget.x + 2
                    yPos = problemWidget.y + 2
                  }
                  return this.generateMCOs(problemWidget, labels, 0, xPos, yPos)
                }}
                deleteMCOs={(nrMCOs) => {
                  let len = props.problem.mc_options.length
                  if (nrMCOs >= len) {
                    return new Promise((resolve, reject) => {
                      this.setState({deletingMCWidget: true}, () => { resolve(false) })
                    })
                  } else if (nrMCOs > 0) {
                    return this.deleteMCOs(selectedWidgetId, len - nrMCOs, nrMCOs)
                  }
                }}
                updateLabels={(labels) => {
                  labels.map((label, index) => {
                    let option = props.problem.mc_options[index]
                    const formData = new window.FormData()
                    formData.append('name', option.widget.name)
                    formData.append('x', option.widget.x + option.cbOffsetX)
                    formData.append('y', option.widget.y + option.cbOffsetY)
                    formData.append('problem_id', props.problem.id)
                    formData.append('label', labels[index])
                    api.patch('mult-choice/' + option.id, formData)
                      .then(() => {
                        this.setState((prevState) => {
                          return {
                            widgets: update(prevState.widgets, {
                              [selectedWidgetId]: {
                                'problem': {
                                  'mc_options': {
                                    [index]: {
                                      label: {
                                        $set: labels[index]
                                      }
                                    }
                                  }
                                }
                              }
                            })
                          }
                        })
                      })
                      .catch(err => {
                        console.log(err)
                        err.json().then(res => {
                          Notification.error('Could not update feedback' +
                            (res.message ? ': ' + res.message : ''))
                          // update to try and get a consistent state
                          this.props.updateExam()
                        })
                      })
                  })
                }}
              />) : null}
            {props.problem &&
              <React.Fragment>
                <div className='panel-block'>
                  {!this.state.editActive && <label className='label'>Feedback options</label>}
                </div>
                <FeedbackPanel examID={this.props.examID} problem={props.problem}
                  editFeedback={this.editFeedback} showTooltips={this.state.showTooltips}
                  grading={false} updateFeedback={this.updateFeedback} />
              </React.Fragment>
            }
          </React.Fragment>
        )}
        {props.problem &&
          <React.Fragment>
            <div className='panel-block mcq-block'>
              <b>Auto-approve</b>
              <Tooltip
                icon='question-circle'
                location='top'
                text='Approve answers automatically. Click for more info.'
                clickAction={() => this.props.setHelpPage('gradingPolicy')}
              />
              <div className='select is-hovered is-fullwidth'>
                <select value={props.problem.grading_policy} onChange={this.onChangeAutoApproveType.bind(this)}>
                  <option value='set_nothing'>Nothing</option>
                  <option value='set_blank'>Blanks</option>
                  {props.problem.mc_options.length !== 0 && <option value='set_single'>One answer</option>}
                </select>
              </div>
            </div>
            <div className='panel-block'>
              <button
                disabled={props.disabledDelete}
                className='button is-danger is-fullwidth'
                onClick={() => props.onDeleteClick()}
              >
                Delete problem
              </button>
            </div>
          </React.Fragment>
        }
      </nav>
    )
  }

  onFinalize = () => {
    this.props.updateExam()
    // needed to enable tabs in navbar
    this.props.updateExamList()
  }

  PanelExamActions = () => {
    if (this.props.exam.finalized) {
      return <PanelGenerate examID={this.state.examID} />
    }

    return (
      <PanelFinalize
        examID={this.props.examID}
        onFinalize={this.onFinalize}
        deleteExam={this.props.deleteExam}>
        <p className='content' dangerouslySetInnerHTML={{__html: ExamFinalizeMarkdown}} />
      </PanelFinalize>
    )
  }

  render () {
    return <React.Fragment>
      <div className='columns is-centered' >
        <div className='column is-one-quarter-fullhd is-one-third-desktop' >
          <PanelExamName
            name={this.props.examName}
            examID={this.state.examID}
            updateExam={this.props.updateExam}
            updateExamList={this.props.updateExamList} />
          <this.SidePanel
            examID={this.state.examID}
            setHelpPage={this.props.setHelpPage} />
        </div>
        <div className='column is-narrow' >
          <div className='editor-content'>
            {this.renderContent()}
          </div>
        </div>
      </div>
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
        onConfirm={() => {
          this.setState({
            deletingMCWidget: false
          })
          this.deleteMCOs(this.state.selectedWidgetId, 0)
        }}
      />
    </React.Fragment>
  }
}

export default ExamTemplated

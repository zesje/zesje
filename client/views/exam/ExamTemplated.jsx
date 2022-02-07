import React from 'react'

import { toast } from 'bulma-toast'
import update from 'immutability-helper'

import GeneratedExamPreview from '../../components/GeneratedExamPreview.jsx'
import PanelGenerate from '../../components/PanelGenerate.jsx'
import PanelMCQ from '../../components/PanelMCQ.jsx'
import ConfirmationModal from '../../components/modals/ConfirmationModal.jsx'
import FeedbackMenu from '../../components/feedback/FeedbackMenu.jsx'
import Tooltip from '../../components/Tooltip.jsx'

import ExamEditor from './ExamEditor.jsx'
import PanelGradeAnonymous from './PanelGradeAnonymous.jsx'
import ExamFinalizeMarkdown from './ExamFinalize.md'
import PanelExamName from './PanelExamName.jsx'
import PanelFinalize from './PanelFinalize.jsx'

import './Exam.scss'

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

const GRADING_POLICY = [
  { id: 'set_nothing', name: 'Nothing', onlyMCQ: false },
  { id: 'set_blank', name: 'Blanks', onlyMCQ: false },
  { id: 'set_single', name: 'One answer', onlyMCQ: true }
]

class ExamTemplated extends React.Component {
  state = {
    examID: null,
    page: 0,
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
            root_feedback_id: problem.root_feedback_id,
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
    }
  }

  componentWillUnmount = () => {
    // This might try to save the name unnecessary, but better twice than never.
    this.saveProblemName()
  }

  updateFeedback = (problemId) => {
    const problemWidget = Object.values(this.state.widgets)
      .find(widget => widget.problem && widget.problem.id === problemId)
    const problemWidgetId = problemWidget.id
    api.get(`problems/${problemId}`).then(problem => {
      this.setState((prevState) => ({
        widgets: {
          ...prevState.widgets,
          [problemWidgetId]: {
            ...prevState.widgets[problemWidgetId],
            problem: {
              ...prevState.widgets[problemWidgetId].problem,
              feedback: problem.feedback,
              root_feedback_id: problem.root_feedback_id
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
   */
  updateFeedbackAtIndex = (feedback, problemWidget) => {
    if (feedback.deleted) {
      // delete the feedback if the deleted field is set
      this.setState((prevState) => {
        return {
          widgets: update(prevState.widgets, {
            [problemWidget.id]: {
              problem: {
                feedback: {
                  $unset: [feedback.id],
                  [problemWidget.problem.root_feedback_id]: { // remove the FO from the children list
                    children: {
                      $set: problemWidget.problem.feedback[problemWidget.problem.root_feedback_id].children
                        .filter(id => id !== feedback.id)
                    }
                  }
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
              problem: {
                feedback: {
                  [feedback.id]: {
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

    api.patch('problems/' + problem.id, { name: problem.name })
      .catch(e => toast({ message: 'Could not save new problem name: ' + e, type: 'is-danger' }))
      .then(this.setState({
        changedWidgetId: null
      }))
  }

  onChangeAutoApproveType = (e) => {
    const selectedWidgetId = this.state.selectedWidgetId
    if (!selectedWidgetId) return

    const selectedWidget = this.state.widgets[selectedWidgetId]
    if (!selectedWidget) return

    const problem = selectedWidget.problem
    if (!problem) return

    const newPolicy = e.target.value

    api.patch('problems/' + problem.id, { grading_policy: newPolicy })
      .then(success => {
        this.setState(prevState => ({
          widgets: update(prevState.widgets, {
            [selectedWidgetId]: {
              problem: {
                grading_policy: {
                  $set: newPolicy
                }
              }
            }
          })
        }))
        if (newPolicy === 'set_single') {
          api.patch(`feedback/${problem.id}/${problem.root_feedback_id}`, { exclusive: true })
            .then(res => {
              this.updateFeedback(problem.id)
              if (res.set_aside_solutions > 0) {
                toast({
                  message: `${res.set_aside_solutions} solution${res.set_aside_solutions > 1 ? 's have' : ' has'} ` +
                    'been marked as ungraded due to incompatible feedback options.',
                  type: 'is-warning',
                  duration: 5000
                })
              }
            })
            .catch(error => console.log(error))
        }
      })
      .catch(error => {
        error.json().then(res => {
          let message = res.message
          if (typeof message === 'object') {
            message = Object.values(message)[0]
          }
          toast({ message: 'Could not change grading policy: ' + message, type: 'is-danger' })
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
            toast({ message: 'Could not delete problem' + (res.message ? ': ' + res.message : ''), type: 'is-danger' })
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
            const feedback = widget.problem.feedback[feedbackId]
            feedback.highlight = true
            this.updateFeedbackAtIndex(feedback, widget)
          }}
          removeHighlight={(widget, feedbackId) => {
            const feedback = widget.problem.feedback[feedbackId]
            feedback.highlight = false
            this.updateFeedbackAtIndex(feedback, widget)
          }}
          removeAllHighlight={(widget) => {
            Object.keys(widget.problem.feedback).forEach((id) => {
              const feedback = widget.problem.feedback[id]
              feedback.highlight = false
              this.updateFeedbackAtIndex(feedback, widget)
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

    const feedback = {
      name: labels[index],
      description: '',
      score: 0
    }

    const data = {
      label: labels[index],
      problem_id: problemWidget.problem.id,
      feedback_id: null,
      cbOffsetX: 7, // checkbox offset relative to option position on x axis
      cbOffsetY: 21, // checkbox offset relative to option position on y axis
      widget: {
        name: 'mc_option_' + labels[index],
        x: xPos,
        y: yPos,
        type: 'mcq_widget'
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
        toast({ message: 'Could not delete problem' + (res.message ? ': ' + res.message : ''), type: 'is-danger' })
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
    const widget = this.state.widgets[widgetId]
    if (nrMCOs <= 0 || !widget.problem.mc_options.length) return Promise.resolve(true)

    const option = widget.problem.mc_options[index]
    if (!option) return Promise.resolve(false)

    console.log(option)
    console.log(widget.problem)
    return api.del('mult-choice/' + option.id)
      .then(res => {
        const feedback = widget.problem.feedback[option.feedback_id]
        feedback.deleted = true
        this.updateFeedbackAtIndex(feedback, widget)
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
          toast({
            message: 'Could not delete multiple choice option' + (res.message ? ': ' + res.message : ''),
            type: 'is-danger'
          })
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
    const newMCO = widget.problem.mc_options.map((option, i) => {
      return {
        widget: {
          x: {
            $set: data.x + i * widget.problem.widthMCO
          },
          y: {
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
          problem: {
            mc_options: newMCO
          }
        }
      })
    }))
  }

  panelEdit = (problem, widgetEditDisabled, widgetDeleteDisabled) => {
    const selectedWidgetId = this.state.selectedWidgetId

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Problem details
        </p>
        {selectedWidgetId === null || !problem
          ? <div className='panel-block'>
            <div className='field'>
              <p>
                To create a problem, draw a rectangle on the exam.
              </p>
            </div>
          </div>
          : <>
            <div className='panel-block'>
              <div className='field' style={{ flexGrow: 1 }}>
                <label className='label'>Name</label>
                <div className='control'>
                  <input
                    disabled={widgetEditDisabled}
                    className='input'
                    placeholder='Problem name'
                    value={problem ? problem.name : ''}
                    onChange={(e) => {
                      this.setState(prevState => ({
                        changedWidgetId: selectedWidgetId,
                        widgets: update(prevState.widgets, {
                          [selectedWidgetId]: {
                            problem: {
                              name: {
                                $set: e.target.value
                              }
                            }
                          }
                        })
                      }))
                    }}
                    onBlur={(e) => {
                      this.saveProblemName(e.target.value)
                    }}
                  />
                </div>
              </div>
            </div>
            {problem && !this.props.exam.finalized
              ? <PanelMCQ
                problem={problem}
                generateMCOs={(labels) => {
                  const problemWidget = this.state.widgets[this.state.selectedWidgetId]
                  let xPos, yPos
                  if (problem.mc_options.length > 0) {
                    // position the new mc options widget next to the last mc options
                    const last = problem.mc_options[problem.mc_options.length - 1].widget
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
                  const len = problem.mc_options.length
                  if (nrMCOs >= len) {
                    return new Promise((resolve, reject) => {
                      this.setState({ deletingMCWidget: true }, () => { resolve(false) })
                    })
                  } else if (nrMCOs > 0) {
                    return this.deleteMCOs(selectedWidgetId, len - nrMCOs, nrMCOs)
                  }
                }}
                updateLabels={(labels) => {
                  labels.forEach((label, index) => {
                    const option = problem.mc_options[index]
                    const formData = new window.FormData()
                    formData.append('name', option.widget.name)
                    formData.append('x', option.widget.x + option.cbOffsetX)
                    formData.append('y', option.widget.y + option.cbOffsetY)
                    formData.append('problem_id', problem.id)
                    formData.append('label', labels[index])
                    api.patch('mult-choice/' + option.id, formData).then(() => {
                      this.setState((prevState) => {
                        return {
                          widgets: update(prevState.widgets, {
                            [selectedWidgetId]: {
                              problem: {
                                mc_options: {
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
                    }).catch(err => {
                      console.log(err)
                      err.json().then(res => {
                        toast({
                          message: 'Could not update feedback' + (res.message ? ': ' + res.message : ''),
                          type: 'is-danger'
                        })
                        // update to try and get a consistent state
                        this.props.updateExam()
                      })
                    })
                  })
                }}
                />
              : null}
            {problem &&
              <>
                <div className='panel-block'>
                  <label className='label'>Feedback options</label>
                </div>
                <FeedbackMenu
                  problem={problem}
                  updateFeedback={() => this.updateFeedback(problem.id)} />
              </>
            }
          </>
        }
        {problem &&
          <>
            <div className='panel-block mcq-block'>
              <b>Auto-approve</b>
              <Tooltip
                icon='question-circle'
                location='top'
                text='Approve answers automatically. Click for more info.'
                clickAction={() => this.props.setHelpPage('gradingPolicy')}
              />
              <div className='select is-hovered is-fullwidth'>
                <select value={problem.grading_policy} onChange={this.onChangeAutoApproveType}>
                  {GRADING_POLICY.filter(policy => !policy.onlyMCQ || problem.mc_options.length !== 0)
                    .map(policy => <option key={policy.id} value={policy.id}>{policy.name}</option>)}
                </select>
              </div>
            </div>
            <div className='panel-block'>
              <button
                disabled={widgetDeleteDisabled}
                className='button is-danger is-fullwidth'
                onClick={() => this.setState({ deletingWidget: true })}
              >
                Delete problem
              </button>
            </div>
          </>}
      </nav>
    )
  }

  onFinalize = () => {
    this.props.updateExam()
    // needed to enable tabs in navbar
    this.props.updateExamList()
  }

  panelExamActions = () => {
    if (this.props.exam.finalized) {
      return <PanelGenerate examID={this.state.examID} />
    }

    return (
      <PanelFinalize
        examID={this.state.examID}
        onFinalize={this.onFinalize}
        deleteExam={this.props.deleteExam}
      >
        <p className='content' dangerouslySetInnerHTML={{ __html: ExamFinalizeMarkdown }} />
      </PanelFinalize>
    )
  }

  render () {
    const selectedWidgetId = this.state.selectedWidgetId
    const selectedWidget = selectedWidgetId && this.state.widgets[selectedWidgetId]
    const problem = selectedWidget && selectedWidget.problem
    const widgetEditDisabled = (this.state.previewing || !problem)
    const isGraded = problem && problem.n_graded > 0
    const widgetDeleteDisabled = widgetEditDisabled || isGraded

    return (
      <>
        <div className='columns is-centered is-multiline'>
          <div className='column is-one-quarter-fullhd is-full-desktop is-full-touch'>
            <PanelExamName
              name={this.props.examName}
              examID={this.state.examID}
              updateExam={this.props.updateExam}
              updateExamList={this.props.updateExamList}
            />
            {this.panelExamActions()}
            {this.props.exam.finalized && <PanelGradeAnonymous
              examID={this.state.examID}
              gradeAnonymous={this.props.exam.gradeAnonymous}
              onChange={(anonymous) => this.props.updateExam()}
              />}
          </div>
          <div className='column is-narrow'>
            <Pager
              page={this.state.page}
              numPages={this.state.numPages}
              setPage={this.setPage}
            />
            <div className='editor-content'>
              {this.renderContent()}
            </div>
          </div>
          <div className='column'>
            {this.panelEdit(problem, widgetEditDisabled, widgetDeleteDisabled)}
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
          onCancel={() => this.setState({ deletingWidget: false })}
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
          onCancel={() => this.setState({ deletingMCWidget: false })}
          onConfirm={() => {
            this.setState({
              deletingMCWidget: false
            })
            this.deleteMCOs(this.state.selectedWidgetId, 0)
          }}
        />
      </>
    )
  }
}

export default ExamTemplated

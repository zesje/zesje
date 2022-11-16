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

const MCO_WIDTH = 20
const MCO_HEIGHT = 34

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
  { id: 'set_single', name: '≤1 answer', onlyMCQ: true }
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
            mc_options: problem.mc_options
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
      this.updateWidget(problemWidgetId, {
        problem: {
          feedback: { $set: problem.feedback },
          root_feedback_id: { $set: problem.root_feedback_id }
        }
      })
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
      this.updateWidget(problemWidget.id, {
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
      })
    } else {
      // update the existing feedback
      this.updateWidget(problemWidget.id, {
        problem: {
          feedback: {
            [feedback.id]: {
              $set: feedback
            }
          }
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
      .then(() => this.setState({ changedWidgetId: null }))
      .catch(e => toast({ message: 'Could not save new problem name: ' + e.message, type: 'is-danger' }))
  }

  onChangeAutoApproveType = (e) => {
    const selectedWidgetId = this.state.selectedWidgetId
    if (!selectedWidgetId) return

    const selectedWidget = this.state.widgets[selectedWidgetId]
    if (!selectedWidget) return

    const problem = selectedWidget.problem
    if (!problem) return

    const oldPolicy = problem.grading_policy
    const newPolicy = e.target.value

    if (oldPolicy === newPolicy) return

    api.patch('problems/' + problem.id, { grading_policy: newPolicy })
      .then(success => {
        this.updateWidget(selectedWidgetId, {
          problem: {
            grading_policy: {
              $set: newPolicy
            }
          }
        })
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
            .catch(console.error)
        } else if (oldPolicy === 'set_single' &&
          problem.mc_options.length > 0 &&
          problem.feedback[problem.root_feedback_id].exclusive) {
          // the problem has multiple choice questions but the grading policy is not set single
          // so change the root feedback to not exclusive
          api.patch(`feedback/${problem.id}/${problem.root_feedback_id}`, { exclusive: false })
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
            .catch(console.error)
        }
      })
      .catch(err => {
        let message = err.message
        if (typeof message === 'object') {
          message = Object.values(message)[0]
        }
        toast({ message: 'Could not change grading policy: ' + message, type: 'is-danger' })
      })
  }

  createNewWidget = (widgetData) => {
    this.setState((prevState) => ({
      selectedWidgetId: widgetData.id,
      widgets: update(prevState.widgets, {
        [widgetData.id]: {
          $set: widgetData
        }
      })
    }))
  }

  deleteWidget = (widgetId) => {
    const widget = this.state.widgets[widgetId]
    if (widget) {
      api.del('problems/' + widget.problem.id)
        .then(() => {
          this.setState((prevState) => ({
            selectedWidgetId: null,
            changedWidgetId: null,
            deletingWidget: false,
            widgets: update(prevState.widgets, {
              $unset: [widgetId]
            })
          }))
        })
        .catch(err => {
          this.setState({ deletingWidget: false })
          toast({ message: 'Could not delete problem' + (err.message ? ': ' + err.message : ''), type: 'is-danger' })
          // update to try and get a consistent state
          this.props.updateExam()
        })
    }
  }

  updateWidget = (widgetId, newData) => this.setState(prevState => ({
    widgets: update(prevState.widgets, {
      [widgetId]: newData
    })
  }))

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
          selectWidget={(widgetId) => this.setState({ selectedWidgetId: widgetId })}
          createNewWidget={this.createNewWidget}
          updateExam={this.props.updateExam}
          widthMCO={MCO_WIDTH}
          heightMCO={MCO_HEIGHT}
        />
      )
    }
  }

  onPDFLoad = (pdf) => this.setState({ numPages: pdf.numPages }, this.props.updateExam)

  setPage = (newPage) => this.setState((prevState) => ({
    // clamp the page
    selectedWidgetId: null,
    page: Math.max(0, Math.min(newPage, prevState.numPages - 1))
  }))

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
      const minWidthMCOs = MCO_WIDTH * (problemWidget.problem.mc_options.length + 1)
      const diff = problemWidget.problem.mc_options[0].widget.x - problemWidget.x
      if (problemWidget.x + problemWidget.width < xPos + MCO_WIDTH) {
        const width = Math.max(minWidthMCOs + diff, 75)
        api.patch('widgets/' + problemWidget.id, { width: width })
          .then(() => this.updateWidget(problemWidget.id, { width: { $set: width } }))
      }
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
      widget: {
        name: 'mc_option_' + labels[index],
        x: xPos,
        y: yPos,
        type: 'mcq_widget'
      }
    }

    // TODO: a lot of duplicates but will change in #672
    const formData = {
      name: data.widget.name,
      x: data.widget.x,
      y: data.widget.y,
      problem_id: data.problem_id,
      label: data.label
    }
    return api.put('mult-choice/', formData).then(result => {
      data.id = result.mult_choice_id
      data.feedback_id = result.feedback_id
      feedback.id = result.feedback_id
      this.addMCOtoState(problemWidget, data)
      this.updateFeedback(problemWidget.problem.id)
      return this.generateMCOs(problemWidget, labels, index + 1, xPos + MCO_WIDTH, yPos)
    }).catch(err => {
      toast({ message: 'Could not delete problem' + (err.message ? ': ' + err.message : ''), type: 'is-danger' })
      // update to try and get a consistent state
      this.props.updateExam()
      this.setState({
        selectedWidgetId: null
      })

      return false
    })
  }

  /**
   * This method creates a mc option widget object and adds it to the corresponding problem in the state
   * @param problemWidget The widget the mc option belongs to
   * @param data the mc option
   */
  addMCOtoState = (problemWidget, data) => this.updateWidget(problemWidget.id, {
    problem: { mc_options: { $push: [data] } }
  })

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
        toast({
          message: 'Could not delete multiple choice option' + (err.message ? ': ' + err.message : ''),
          type: 'is-danger'
        })
        // update to try and get a consistent state
        this.props.updateExam()
        this.setState({
          selectedWidgetId: null
        })
        return Promise.resolve(false)
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
            $set: data.x + i * MCO_WIDTH
          },
          y: {
            // each mc option needs to be positioned next to the previous option and should not overlap it
            $set: data.y
          }
        }
      }
    })

    // update the state with the new locations
    this.updateWidget(widget.id, { problem: { mc_options: newMCO } })
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
                    onBlur={this.saveProblemName}
                  />
                </div>
              </div>
            </div>
            {problem && !this.props.exam.finalized
              ? <PanelMCQ
                problem={problem}
                generateMCOs={(labels) => {
                  const problemWidget = this.state.widgets[selectedWidgetId]
                  let xPos, yPos
                  if (problem.mc_options.length > 0) {
                    // position the new mc options widget next to the last mc options
                    const last = problem.mc_options[problem.mc_options.length - 1].widget
                    xPos = last.x + MCO_WIDTH
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
                    api.patch('mult-choice/' + option.id, { label: labels[index] })
                      .then(() => {
                        this.updateWidget(selectedWidgetId, {
                          problem: {
                            mc_options: {
                              [index]: {
                                label: { $set: labels[index] }
                              }
                            }
                          }
                        })
                      }).catch(err => {
                        toast({
                          message: 'Could not update feedback' + (err.message ? ': ' + err.message : ''),
                          type: 'is-danger'
                        })
                        // update to try and get a consistent state
                        this.props.updateExam()
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
          headerText={`Are you sure you want to delete problem "${problem && problem.name}"`}
          confirmText='Delete problem'
          onCancel={() => this.setState({ deletingWidget: false })}
          onConfirm={() => this.deleteWidget(this.state.selectedWidgetId)}
        />
        <ConfirmationModal
          active={this.state.deletingMCWidget && this.state.selectedWidgetId != null}
          color='is-danger'
          headerText={
            `Are you sure you want to delete the multiple choice options for problem "${problem && problem.name}"`}
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

import React from 'react'

import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'
import './Exam.css'
import GeneratedExamPreview from '../components/GeneratedExamPreview.jsx'
import PanelGenerate from '../components/PanelGenerate.jsx'
import ExamEditor from './ExamEditor.jsx'
import update from 'immutability-helper'
import ExamFinalizeMarkdown from './ExamFinalize.md'
import ConfirmationModal from '../components/ConfirmationModal.jsx'
import FeedbackPanel from './grade/FeedbackPanel.jsx'
import EditPanel from './grade/EditPanel.jsx'

import * as api from '../api.jsx'

class Exams extends React.Component {
  state = {
    examID: null,
    page: 0,
    editActive: false,
    feedbackToEdit: null,
    numPages: null,
    selectedWidgetId: null,
    changedWidgetId: null,
    widgets: [],
    previewing: false,
    deletingExam: false,
    deletingWidget: false
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
            feedback: problem.feedback || []
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
    // This is a rough update for when feedback is edited.
    newProps.exam.problems.forEach(problem => {
      prevState.widgets[problem.widget.id].problem.feedback = problem.feedback
    })
    return prevState
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
    if (!this.state.deletingExam) {
      this.props.updateExam(this.props.examID)
    }
  }

  editFeedback = (feedback) => {
    this.setState({
      editActive: true,
      feedbackToEdit: feedback
    })
  }
  backToFeedback = () => {
    this.props.updateExam(this.props.exam.id)
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

    api.put('problems/' + problem.id + '/name', { name: problem.name })
      .catch(e => Notification.error('Could not save new problem name: ' + e))
      .then(this.setState({
        changedWidgetId: null
      }))
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
          createNewWidget={(widgetData) => {
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

  SidePanel = (props) => {
    const selectedWidgetId = this.state.selectedWidgetId
    let selectedWidget = selectedWidgetId && this.state.widgets[selectedWidgetId]
    let problem = selectedWidget && selectedWidget.problem
    let widgetEditDisabled = this.state.previewing || !problem
    let isGraded = problem && problem.graded
    let widgetDeleteDisabled = widgetEditDisabled || isGraded

    return (
      <React.Fragment>
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
        />
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
        <div className='panel-block'>
          <div className='field'>
            {selectedWidgetId === null ? (
              <p style={{margin: '0.625em 0', minHeight: '3em'}}>
                To create a problem, draw a rectangle on the exam.
              </p>
            ) : (
              <React.Fragment>
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
                    }} />
                  {this.state.editActive
                    ? <EditPanel problemID={props.problem.id} feedback={this.state.feedbackToEdit}
                      goBack={this.backToFeedback} />
                    : <FeedbackPanel examID={this.props.examID} problem={props.problem}
                      editFeedback={this.editFeedback} showTooltips={this.state.showTooltips}
                      grading={false}
                    />}
                </div>
              </React.Fragment>
            )}
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
    </div>
  }
}

export default Exams

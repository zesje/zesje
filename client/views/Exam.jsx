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

import * as api from '../api.jsx'

class Exams extends React.Component {
  state = {
    examID: null,
    page: 0,
    numPages: null,
    selectedWidgetId: null,
    widgets: [],
    previewing: false,
    deleting: false
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
            name: problem.name
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
        widgets: widgets,
        previewing: false
      }
    }

    return null
  }

  componentDidUpdate = (prevProps) => {
    if (prevProps.examID !== this.props.examID) {
      this.props.updateExam(this.props.examID)
    }
  }

  componentDidMount = () => {
    if (this.props.examID !== this.props.exam.id) this.props.updateExam(this.props.examID)
  }

  componentWillUnmount = () => {
    // This might save the name unnecessary, but better twice than never.
    // We could keep track in state if we need to save the name when the double requests cause issues
    this.saveProblemName()
    // Force an update of the upper exam state, since this component does not update and use that correctly
    this.props.updateExam(this.props.examID)
  }

  saveProblemName = () => {
    const selectedWidgetId = this.state.selectedWidgetId
    if (!selectedWidgetId) return

    const selectedWidget = this.state.widgets[selectedWidgetId]
    if (!selectedWidget) return

    const problem = selectedWidget.problem
    if (!problem) return

    api.put('problems/' + problem.id + '/name', { name: problem.name })
      .catch(e => Notification.error('Could not save new problem name: ' + e))
  }

  deleteWidget = (widgetId, prompt = true) => {
    const widget = this.state.widgets[widgetId]
    if (widget) {
      if (prompt && confirm('Are you sure you want to delete this widget?')) {
        api.del('problems/' + widget.problem.id)
          .then(() => {
            this.setState((prevState) => {
              return {
                selectedWidgetId: null,
                widgets: update(prevState.widgets, {
                  $unset: [widgetId]
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

    return (
      <React.Fragment>
        <this.PanelEdit
          disabled={widgetEditDisabled}
          onDeleteClick={() => {
            this.deleteWidget(selectedWidgetId)
          }}
          problem={problem}
          changeProblemName={newName => {
            this.setState(prevState => ({
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
    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Problem details
        </p>
        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Name</label>
            <div className='control'>
              <input
                disabled={props.disabled}
                className='input'
                placeholder='Problem name'
                value={props.problem ? props.problem.name : ''}
                onChange={(e) => {
                  console.log('onChange')
                  props.changeProblemName(e.target.value)
                }}
                onBlur={(e) => {
                  console.log('onBlur')
                  props.saveProblemName(e.target.value)
                }} />
            </div>
          </div>
        </div>
        <div className='panel-block'>
          <button
            disabled={props.disabled}
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
        onClick={() => { this.setState({deleting: true}) }}
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
        active={this.state.deleting}
        color='is-danger'
        headerText={`Are you sure you want to delete exam "${this.props.exam.name}"?`}
        confirmText='Delete exam'
        onCancel={() => this.setState({deleting: false})}
        onConfirm={() => {
          this.props.deleteExam(this.props.examID).then(this.props.leave)
        }}
      />
    </div>
  }
}

export default Exams

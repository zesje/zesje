import React from 'react'
import { toast } from 'bulma-toast'

import FeedbackMenu from '../../components/feedback/FeedbackMenu.jsx'
import { HasModalContext } from '../../components/feedback/FeedbackUtils.jsx'
import ConfirmationModal from '../../components/modals/ConfirmationModal.jsx'
import ExamUnstructuredRules from './ExamUnstructuredRules.md'
import PanelGradeAnonymous from './PanelGradeAnonymous.jsx'
import PanelExamName from './PanelExamName.jsx'
import PanelFinalize from './PanelFinalize.jsx'

import * as api from '../../api.jsx'

const groupBy = (array, key) =>
  array.reduce((objectsByKeyValue, obj) => {
    const value = obj[key]
    objectsByKeyValue[value] = (objectsByKeyValue[value] || []).concat(obj)
    return objectsByKeyValue
  }, {})

const ExamContent = (props) => {
  const problemCount = props.problems.length
  const pages = problemCount > 0 ? groupBy(props.problems, 'page') : { 0: [] }

  const pageCount = Object.keys(pages).length
  const pageTitle = pageCount === 1 && 'Problem list'
  const addPageButtonText = pageCount === 1 ? 'Specify pages' : 'Add page'

  return (
    <>
      {Object.keys(pages).map(page => (
        <div className='card page-card' key={page}>
          <header className='card-header'>
            <p className='card-header-title'>
              {pageTitle || `Page ${(parseInt(page) + 1)}`}
            </p>
            <a
              className='card-header-icon'
              onClick={() => props.createProblem(parseInt(page))}
            >
              <span className='icon is-medium'>
                <i className='fa fa-plus ' />
              </span>
              <span>Add problem</span>
            </a>
          </header>
          <div className='card-content'>
            <div className='content'>
              {problemCount
                ? pages[page].map(p => (
                <button
                  className={'button problem is-fullwidth ' +
                                    (props.selectedProblemId === p.id ? 'is-primary' : '')}
                  onClick={() => props.selectProblem(p.id)}
                  key={p.id}
                >
                  {p.name}
                </button>
                ))
                : <p>No problems</p>}
            </div>
          </div>
        </div>
      ))}
      {problemCount && !props.finalized
        ? <button
        className='button problem is-link is-fullwidth'
        onClick={props.addPage}
                                          >
        <span>{addPageButtonText}</span>
                                          </button>
        : null}
    </>
  )
}

class ExamUnstructured extends React.Component {
  state = {
    exam: null,
    problems: [],
    problemName: '',
    problemPage: -1,
    selectedProblemId: null,
    deletingProblem: false
  }

  static getDerivedStateFromProps = (newProps, prevState) => {
    if (prevState.exam !== newProps.exam) {
      const problems = newProps.exam.problems.sort((p1, p2) => p1.page - p2.page)
      let problem = problems.find(p => p.id === prevState.selectedProblemId)
      if (!problem && problems.length > 0) {
        problem = problems[0]
      }

      return {
        exam: newProps.exam,
        problems,
        selectedProblemId: problem ? problem.id : null,
        problemName: problem ? problem.name : null,
        problemPage: problem ? problem.page + 1 : -1,
        deletingProblem: false
      }
    }

    return null
  }

  componentWillUnmount = () => {
    // This might try to save the name unnecessary, but better twice than never.
    if (this.selectedProblemId !== null) {
      this.saveProblemPage()
      this.saveProblemName()
    }
  }

  selectProblem = (id) => {
    let problem = this.state.problems.find(p => p.id === id)
    if (!problem && this.state.problems.length > 0) {
      problem = this.state.problems[0]
    }

    this.setState({
      selectedProblemId: problem ? problem.id : null,
      problemName: problem ? problem.name : null,
      problemPage: problem ? problem.page + 1 : -1,
      deletingProblem: false
    })
  }

  addPage = () => {
    const lastPage = this.state.problems.length > 0 ? this.state.problems[this.state.problems.length - 1].page : -1
    this.createProblem(lastPage + 1)
  }

  createProblem = (page) => {
    const jsonData = {
      exam_id: this.props.examID,
      name: `Problem (${this.state.problems.length + 1})`,
      page,
      x: 0,
      y: 0,
      width: 0,
      height: 0
    }
    api.post('problems', jsonData).then(result =>
      this.setState({ selectedProblemId: result.id }, this.props.updateExam)
    ).catch(console.error)
  }

  saveProblemName = (id, name) => {
    if (!name) {
      this.selectProblem(id)
      return
    }

    api.patch('problems/' + id, { name })
      .then(resp => this.props.updateExam())
      .catch(err => {
        this.selectProblem(id) // takes care of updating the problem name to previous state
        toast({ message: 'Could not save new problem name: ' + err.message, type: 'is-danger' })
      })
  }

  saveProblemPage = (problemId, widgetId, page) => {
    if (!page) {
      this.selectProblem(problemId)
      return
    }

    api.patch(`widgets/${widgetId}`, { page: parseInt(page) - 1 })
      .then(resp => this.props.updateExam())
      .catch(err => {
        this.props.updateExam()
        toast({ message: 'Could not save new problem page: ' + err.message, type: 'is-warning' })
      })
  }

  deleteProblem = (id) => {
    api.del('problems/' + id)
      .then(this.props.updateExam)
      .catch(err => {
        this.setState({ deletingProblem: false })
        toast({ message: 'Could not delete problem' + (err.message ? ': ' + err.message : ''), type: 'is-danger' })
      })
  }

  inputColor = (name, originalName) => {
    if (name) {
      return name !== originalName ? 'is-success' : ''
    } else {
      return 'is-danger'
    }
  }

  updatePage = (newPage) => {
    const patt = /^(-|(-?[1-9]\d*))?$/

    if (patt.test(newPage)) {
      this.setState({
        problemPage: newPage
      })
    }
  }

  onFinalize = () => {
    this.props.updateExam()
    // needed to enable tabs in navbar
    this.props.updateExamList()
  }

  panelProblem = (problem) => {
    return (
        <nav className='panel'>
          <p className='panel-heading'>
            Problem details
          </p>

          {problem
            ? <>
              <div className='panel-block'>
                <div className='field' style={{ flexGrow: 1 }}>
                  <label className='label'>Name</label>
                  <div className='control'>
                    <input
                      className={'input ' + this.inputColor(this.state.problemName, problem.name)}
                      placeholder='Problem name'
                      value={this.state.problemName}
                      onChange={(e) => this.setState({ problemName: e.target.value })}
                      onBlur={(e) => {
                        this.saveProblemName(problem.id, this.state.problemName)
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className='panel-block'>
                <div className='field' style={{ flexGrow: 1 }}>
                  <label className='label'>Page</label>
                  <div className='control'>
                    <input
                      className={'input ' + this.inputColor(this.state.problemPage, problem.page + 1)}
                      placeholder='#'
                      maxLength={2}
                      value={this.state.problemPage}
                      onChange={(e) => this.updatePage(e.target.value)}
                      onBlur={(e) => {
                        this.saveProblemPage(problem.id, problem.widget.id, this.state.problemPage)
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className='panel-block'>
                {!this.state.editActive && <label className='label'>Feedback options</label>}
              </div>
              <HasModalContext.Provider value={(hasModal) => {}}>
                <FeedbackMenu
                  problem={problem}
                  updateFeedback={this.props.updateExam} />
              </HasModalContext.Provider>

              <div className='panel-block'>
                <button
                  disabled={problem.n_graded > 0}
                  className='button is-danger is-fullwidth'
                  onClick={() => this.setState({ deletingProblem: true })}
                >
                  Delete problem
                </button>
              </div>
              </>
            : (
              <div className='panel-block'>
                  <p>Select a problem on the right panel or add a new one.</p>
                </div>
              )}
        </nav>
    )
  }

  render = () => {
    const problem = this.state.problems.find(p => p.id === this.state.selectedProblemId)

    return (
      <>
        <div className='columns is-centered is-multiline'>
          <div className='column is-one-third-fullhd is-two-thirds-tablet'>
            <PanelExamName
              name={this.state.exam.name}
              examID={this.props.examID}
              updateExam={this.props.updateExam}
              updateExamList={this.props.updateExamList}
            />

            <PanelGradeAnonymous
              examID={this.props.examID}
              gradeAnonymous={this.state.exam.gradeAnonymous}
              text='Student name or number may still be visible on the pages themselves.'
            />

            {!this.state.exam.finalized &&
              <PanelFinalize
                examID={this.props.examID}
                onFinalize={this.onFinalize}
                deleteExam={this.props.deleteExam}
              >
                Finalized exams cannot be deleted.
                Take care to not delete or add pages after finalization.
              </PanelFinalize>}

            <nav className='panel'>
              <p className='panel-heading'>
                Tips
              </p>

              <div className='panel-block'>
                <p className='content' dangerouslySetInnerHTML={{ __html: ExamUnstructuredRules }} />
              </div>
            </nav>
          </div>
          <div className='column is-one-third-fullhd is-half-tablet'>
            <div className='editor-content'>
              <ExamContent
                problems={this.state.problems}
                selectedProblemId={this.state.selectedProblemId}
                selectProblem={this.selectProblem}
                createProblem={this.createProblem}
                addPage={this.addPage}
                finalized={this.state.finalized}
              />
            </div>
          </div>
          <div className='column is-one-third-fullhd is-half-tablet'>
            {this.panelProblem(problem)}
          </div>
        </div>
        {problem && <ConfirmationModal
          active={this.state.deletingProblem && this.state.selectedProblemId != null}
          color='is-danger'
          headerText={`Are you sure you want to delete problem "${problem.name}?"`}
          confirmText='Delete problem'
          onCancel={() => this.setState({ deletingProblem: false })}
          onConfirm={() => this.deleteProblem(this.state.selectedProblemId)}
                    />}
      </>
    )
  }
}

export default ExamUnstructured

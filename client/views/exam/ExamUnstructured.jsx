import React from 'react'
import Notification from 'react-bulma-notification'

import FeedbackPanel from '../../components/feedback/FeedbackPanel.jsx'
import ConfirmationModal from '../../components/ConfirmationModal.jsx'
import * as api from '../../api.jsx'

const groupBy = (array, key) =>
  array.reduce((objectsByKeyValue, obj) => {
    const value = obj[key]
    objectsByKeyValue[value] = (objectsByKeyValue[value] || []).concat(obj)
    return objectsByKeyValue
  }, {})

const ExamContent = (props) => {
  if (props.problems.length === 0) {
    return <p className='is-size-5 has-text-centered'>No problems</p>
  }

  const pages = groupBy(props.problems, 'page')
  return (
    <div>
      {Object.keys(pages).map(page => (
        <div className='card'>
          <header className='card-header'>
            <p class='card-header-title'>
              {'Page ' + page}
            </p>
          </header>
          <div className='card-content'>
            <div className='content'>
              {pages[page].map(p => (
                <a className={'button is-fullwidth ' + (props.selectedProblemId === p.id ? 'is-info is-outlined' : '')}
                  onClick={() => props.selectProblem(p.id)}
                >
                  {p.name}
                </a>
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

class PanelEditUnstructured extends React.Component {
  state = {
    examID: null,
    problems: [],
    problemName: '',
    problemPage: -1,
    selectedProblemId: null,
    deletingProblem: false
  }

  componentWillMount = () => {
    if (!this.state.examID && this.props.examID !== this.state.examID) {
      this.setState({examID: this.props.examID}, () => {
        this.loadProblems(null)
      })
    }
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.props.examID !== prevProps.examID) {
      this.setState({examID: this.props.examID})
      this.loadProblems(null)
    }
  }

  loadProblems = (selectId) => {
    api.get('exams/' + this.state.examID)
      .then(exam => {
        this.setState({
          problems: exam.problems.sort((p1, p2) => p1.page - p2.page)
        })
        this.selectProblem(selectId)
      })
      .catch(err => {
        console.log(err)
        err.json().then(res => {
          this.setState({
            problems: [],
            selectedProblemId: null,
            problemName: '',
            deleteProblem: false
          })
        })
      })
  }

  selectProblem = (id) => {
    let problem = this.state.problems.find(p => p.id === id)
    if (!problem && this.state.problems.length > 0) {
      problem = this.state.problems[0]
    }

    this.setState({
      selectedProblemId: problem ? problem.id : null,
      problemName: problem ? problem.name : null,
      problemPage: problem ? problem.page : -1,
      deletingProblem: false
    })
  }

  createProblem = () => {
    const formData = new window.FormData()
    formData.append('exam_id', this.state.examID)
    formData.append('name', `Problem (${this.state.problems.length + 1})`)
    formData.append('page', this.state.problems.length)
    formData.append('x', 0)
    formData.append('y', 0)
    formData.append('width', 0)
    formData.append('height', 0)
    api.post('problems', formData).then(result => {
      this.loadProblems(result.id)
    }).catch(err => {
      console.log(err)
    })
  }

  saveProblemName = (id, name) => {
    api.put('problems/' + id, { name: name })
      .then(resp => this.loadProblems(id))
      .catch(e => {
        this.selectProblem(id) // takes care of updating the problem name to previous state
        console.log(e)
        e.json().then(err => Notification.error('Could not save new problem name: ' + err.message))
      })
  }

  saveProblemPage = (problemId, widgetId, page) => {
    api.patch(`widgets/${widgetId}`, {page: page})
      .then(resp => this.loadProblems(problemId))
      .catch(e => {
        this.selectProblem(problemId)
        console.log(e)
        e.json().then(err => Notification.error('Could not save new problem page: ' + err.message))
      })
  }

  deleteProblem = (id) => {
    api.del('problems/' + id)
      .then(() => {
        this.loadProblems(null)
      })
      .catch(err => {
        console.log(err)
        err.json().then(res => {
          this.setState({
            deletingProblem: false
          })
          Notification.error('Could not delete problem' +
            (res.message ? ': ' + res.message : ''))
        })
      })
  }

  inputColor = (name, originalName) => {
    if (name) {
      if (name !== originalName) {
        return 'is-success'
      } else {
        return 'is-link'
      }
    } else {
      return 'is-danger'
    }
  }

  updatePage = (newPage) => {
    const patt = new RegExp(/^(-|(-?[1-9]\d*)|0)?$/)

    if (patt.test(newPage)) {
      this.setState({
        page: parseInt(newPage)
      })
    }
  }

  PanelProblem = (props) => {
    return (
      (
        <nav className='panel'>
          <p className='panel-heading'>
            Problems
          </p>

          <div className='panel-block'>
            <button className='button is-link is-fullwidth' onClick={() => this.createProblem()}>
              <span>New Problem</span>
            </button>
          </div>

          {props.problem &&
            <React.Fragment>
              <div className='panel-block'>
                <div className='field' style={{flexGrow: 1}}>
                  <label className='label'>Name</label>
                  <div className='control'>
                    <input
                      className={'input ' + this.inputColor(this.state.problemName, props.problem.name)}
                      placeholder='Problem name'
                      value={this.state.problemName}
                      onChange={(e) => this.setState({problemName: e.target.value})}
                      onBlur={(e) => {
                        this.saveProblemName(props.problem.id, this.state.problemName)
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className='panel-block'>
                <div className='field' style={{flexGrow: 1}}>
                  <label className='label'>Page</label>
                  <div className='control'>
                    <input
                      className={'input ' + this.inputColor(this.state.problemPage, props.problem.page)}
                      placeholder='#'
                      value={this.state.problemPage}
                      onChange={(e) => this.updatePage(e.target.value)}
                      onBlur={(e) => {
                        this.saveProblemPage(props.problem.id, props.problem.widget.id, this.state.problemPage)
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className='panel-block'>
                {!this.state.editActive && <label className='label'>Feedback options</label>}
              </div>
              <FeedbackPanel
                examID={this.state.examID}
                problem={props.problem}
                grading={false}
                updateFeedback={() => this.loadProblems(props.problem.id)} />

              <div className='panel-block'>
                <button
                  disabled={props.problem.n_graded > 0}
                  className='button is-danger is-fullwidth'
                  onClick={() => this.setState({deletingProblem: true})}
                >
                  Delete problem
                </button>
              </div>
            </React.Fragment>
          }
        </nav>
      )
    )
  }

  render = () => {
    const problem = this.state.problems.find(p => p.id === this.state.selectedProblemId)

    return (
      <React.Fragment>
        <div className='columns is-centered' >
          <div className='column editor-side-panel is-one-quarter-fullhd is-one-third-desktop' >
            <this.PanelProblem
              problem={problem} />
          </div>
          <div className='column is-two-quarter-fullhd is-one-third-desktop editor-content' >
            <ExamContent
              problems={this.state.problems}
              selectedProblemId={this.state.selectedProblemId}
              selectProblem={this.selectProblem} />
          </div>
        </div>
        {problem && <ConfirmationModal
          active={this.state.deletingProblem && this.state.selectedProblemId != null}
          color='is-danger'
          headerText={`Are you sure you want to delete problem "${problem.name}?"`}
          confirmText='Delete problem'
          onCancel={() => this.setState({deletingProblem: false})}
          onConfirm={() => this.deleteProblem(this.state.selectedProblemId)}
        />}
      </React.Fragment>
    )
  }
}

export default PanelEditUnstructured

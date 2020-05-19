import React from 'react'
import Notification from 'react-bulma-notification'

import FeedbackPanel from '../../components/feedback/FeedbackPanel.jsx'
import ConfirmationModal from '../../components/ConfirmationModal.jsx'
import * as api from '../../api.jsx'

class PanelEditUnstructured extends React.Component {
  state = {
    problems: [],
    problemName: '',
    selectedProblemId: null,
    deletingProblem: false
  }

  componentWillMount () {
    this.loadProblems(null)
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.props.examID !== prevProps.examID) {
      this.loadProblems(null)
    }
  }

  loadProblems = (selectId) => {
    api.get('exams/' + this.props.examID)
      .then(exam => {
        console.log(exam.problems)
        this.setState({
          problems: exam.problems
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
      deletingProblem: false
    })
  }

  createProblem = () => {
    const formData = new window.FormData()
    formData.append('exam_id', this.props.examID)
    formData.append('name', `Problem (${this.state.problems.length + 1})`)
    formData.append('page', 0)
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
        Notification.error('Could not save new problem name: ' + e)
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

  render = () => {
    let problem = this.state.problems.find(p => p.id === this.state.selectedProblemId)

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Problem details
        </p>

        <div className='panel-block'>
          <div className='field is-fullwidth'>
            <label className='label'>Problems</label>
            <div className='field has-addons'>
              <p className='control is-expanded'>
                <span className='select is-fullwidth'>
                  <select
                    onChange={(e) => this.selectProblem(parseInt(e.target.value))}
                    value={this.state.selectedProblemId}
                  >
                    {this.state.problems.length > 0 ? this.state.problems.map((p, index) => {
                      return (
                        <option
                          key={`key_${index}`}
                          value={p.id}
                        >
                          {p.name}
                        </option>
                      )
                    }) : null}
                  </select>
                </span>
              </p>
              <p className='control'>
                <a className='button is-link' onClick={() => this.createProblem()}>
                  <span className='icon is-small'>
                    <i className='fa fa-plus' />
                  </span>
                  <span>Add</span>
                </a>
              </p>
            </div>
          </div>
        </div>

        {problem ? (
          <React.Fragment>
            <div className='panel-block'>
              <div className='field' style={{flexGrow: 1}}>
                <label className='label'>Name</label>
                <div className='control'>
                  <input
                    className={'input' + this.inputColor(this.state.problemName, problem.name)}
                    placeholder='Problem name'
                    value={this.state.problemName}
                    onChange={(e) => this.setState({problemName: e.target.value})}
                    onBlur={(e) => {
                      this.saveProblemName(this.state.selectedProblemId, e.target.value)
                    }}
                  />
                </div>
              </div>
            </div>

            <div className='panel-block'>
              {!this.state.editActive && <label className='label'>Feedback options</label>}
            </div>
            <FeedbackPanel
              examID={this.props.examID}
              problem={problem}
              grading={false}
              updateFeedback={() => this.loadProblems(this.state.selectedProblemId)} />

            <div className='panel-block'>
              <button
                disabled={problem.n_graded > 0}
                className='button is-danger is-fullwidth'
                onClick={() => this.deleteProblem(this.state.selectedProblemId)}
              >
                Delete problem
              </button>
            </div>

            <ConfirmationModal
              active={this.state.deletingProblem && this.state.selectedProblemId != null}
              color='is-danger'
              headerText={`Are you sure you want to delete problem "${problem.name}"`}
              confirmText='Delete problem'
              onCancel={() => this.setState({deletingProblem: false})}
              onConfirm={() => this.deleteProblem(this.state.selectedProblemId)}
            />
          </React.Fragment>
        ) : (
          <div className='panel-block'>
            Click the + button above to add a problem to the exam.
          </div>
        )
        }

      </nav>
    )
  }
}

export default PanelEditUnstructured

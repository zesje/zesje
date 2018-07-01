import React from 'react'

import Hero from '../components/Hero.jsx'

import FeedbackPanel from './grade/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import EditPanel from './grade/EditPanel.jsx'
import SubmissionField from './grade/SubmissionField.jsx'

const ProgressBar = () => null

class Grade extends React.Component {
  state = {
    editActive: false,
    editFeedback: null,
    sIndex: 0,
    pIndex: 0,
    examID: null,
    fullPage: false
  }

  prev = () => {
    const newIndex = this.state.sIndex - 1

    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState({
        sIndex: newIndex
      })
      this.props.updateSubmission(newIndex)
    }
  }
  next = () => {
    const newIndex = this.state.sIndex + 1

    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState({
        sIndex: newIndex
      })
      this.props.updateSubmission(newIndex)
    }
  }

  prevUngraded = () => {
    for (let i = this.state.sIndex - 1; i >= 0; i--) {
      if (this.props.exam.submissions[i].problems[this.state.pIndex].graded_by === null) {
        this.setState({
          sIndex: i
        })
        this.props.updateSubmission(i)
        return
      }
    }
  }
  nextUngraded = () => {
    for (let i = this.state.sIndex + 1; i < this.props.exam.submissions.length; i++) {
      if (this.props.exam.submissions[i].problems[this.state.pIndex].graded_by === null) {
        this.setState({
          sIndex: i
        })
        this.props.updateSubmission(i)
        return
      }
    }
  }

  toggleEdit = () => {
    this.setState({
      editActive: !this.state.editActive,
      editFeedback: null
    }, () => {
      if (!this.state.editActive) this.props.updateExam(this.props.exam.id)
    })
  }

  setSubmission = (id) => {
    const i = this.props.exam.submissions.findIndex(sub => sub.id === id)

    if (i >= 0) {
      this.props.updateSubmission(i)
      this.setState({
        sIndex: i
      })
    }
  }
  changeProblem = (event) => {
    this.setState({
      pIndex: event.target.value
    })
  }

  toggleFullPage = (event) => {
    this.setState({
      fullPage: event.target.checked
    })
  }

  static getDerivedStateFromProps = (newProps, prevState) => {
    if (newProps.exam.id !== prevState.examID && newProps.exam.submissions.length) {
      return {
        sIndex: 0,
        pIndex: 0,
        examID: newProps.exam.id
      }
    }
    return null
  }

  render () {
    const exam = this.props.exam
    const submission = exam.submissions[this.state.sIndex]
    const solution = submission.problems[this.state.pIndex]
    const problem = exam.problems[this.state.pIndex]

    return (
      <div>

        <Hero title='Grade' subtitle='Assign feedback to each solution' />

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                <ProblemSelector problems={exam.problems} changeProblem={this.changeProblem} />
                {this.state.editActive
                  ? <EditPanel problem={problem} editFeedback={this.state.editFeedback} toggleEdit={this.toggleEdit} />
                  : <FeedbackPanel examID={exam.id} submissionID={submission.id}
                    problem={problem} solution={solution} graderID={this.props.graderID}
                    toggleEdit={this.toggleEdit} updateSubmission={() => this.props.updateSubmission(this.state.sIndex)} />
                }
              </div>

              <div className='column'>
                <div className='level'>
                  <div className='level-item'>
                    <div className='field has-addons is-mobile'>
                      <div className='control'>
                        <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                          onClick={this.prevUngraded}>ungraded</button>
                        <button type='submit' className='button is-link'
                          onClick={this.prev}>Previous</button>
                      </div>
                      <div className='control'>
                        <SubmissionField
                          submission={submission}
                          submissions={exam.submissions}
                          setSubmission={this.setSubmission}
                        />
                      </div>
                      <div className='control'>
                        <button type='submit' className='button is-link'
                          onClick={this.next}>Next</button>
                        <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                          onClick={this.nextUngraded}>ungraded</button>
                      </div>
                    </div>
                  </div>
                </div>

                <ProgressBar submissions={exam.submissions} />

                <p className='box'>
                  <img src={exam.id ? ('api/images/solutions/' + exam.id + '/' +
                    problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) : ''} alt='' />
                </p>

                {solution.graded_at
                  ? <div>Graded by: {solution.graded_by.name} <i>({solution.graded_at})</i></div>
                  : <div>Ungraded</div>
                }

                <label className='checkbox'>
                  <input checked={this.state.fullPage} onChange={this.toggleFullPage} type='checkbox' />
                  View full page
                </label>

              </div>
            </div>
          </div>
        </section>

      </div>
    )
  }
}

export default Grade

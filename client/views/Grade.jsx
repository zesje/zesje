import React from 'react'
import Mousetrap from 'mousetrap'

import Hero from '../components/Hero.jsx'

import FeedbackPanel from './grade/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import EditPanel from './grade/EditPanel.jsx'
import SearchBox from '../components/SearchBox.jsx'
import ProgressBar from '../components/ProgressBar.jsx'

class Grade extends React.Component {
  state = {
    editActive: false,
    feedbackToEdit: null,
    sIndex: 0,
    pIndex: 0,
    examID: null,
    fullPage: false
  }

  componentWillUnmount = () => {
    Mousetrap.unbind(['left', 'h'])
    Mousetrap.unbind(['right', 'l'])
    Mousetrap.unbind(['shift+left', 'shift+h'])
    Mousetrap.unbind(['shift+right', 'shift+l'])
    Mousetrap.unbind(['shift+up', 'shift+k'])
    Mousetrap.unbind(['shift+down', 'shift+j'])
  }

  componentDidMount = () => {
    Mousetrap.bind(['left', 'h'], this.prev)
    Mousetrap.bind(['right', 'l'], this.next)
    Mousetrap.bind(['shift+left', 'shift+h'], (event) => {
      event.preventDefault()
      this.prevUngraded()
    })
    Mousetrap.bind(['shift+right', 'shift+l'], (event) => {
      event.preventDefault()
      this.nextUngraded()
    })
    Mousetrap.bind(['shift+up', 'shift+k'], (event) => {
      event.preventDefault()
      this.prevProblem()
    })
    Mousetrap.bind(['shift+down', 'shift+j'], (event) => {
      event.preventDefault()
      this.nextProblem()
    })
  }

  /*
   * This updates the submission to a new one.
   */
  setSubmissionIndex = (newIndex) => {
    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState({
        sIndex: newIndex
      })
      this.props.updateSubmission(newIndex)
      // Also update the exam to get an update of the rubric if there is one.
      this.props.updateExam(this.props.exam.id)
    }
  }

  prev = () => {
    const newIndex = this.state.sIndex - 1
    this.setSubmissionIndex(newIndex)
  }
  next = () => {
    const newIndex = this.state.sIndex + 1
    this.setSubmissionIndex(newIndex)
  }

  prevUngraded = () => {
    for (let i = this.state.sIndex - 1; i >= 0; i--) {
      if (this.props.exam.submissions[i].problems[this.state.pIndex].graded_by === null) {
        this.setSubmissionIndex(i)
        return
      }
    }
  }

  nextUngraded = () => {
    for (let i = this.state.sIndex + 1; i < this.props.exam.submissions.length; i++) {
      if (this.props.exam.submissions[i].problems[this.state.pIndex].graded_by === null) {
        this.setSubmissionIndex(i)
        return
      }
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

  setSubmission = (id) => {
    const i = this.props.exam.submissions.findIndex(sub => sub.id === id)
    this.setSubmissionIndex(i)
  }
  changeProblem = (event) => {
    this.setState({
      pIndex: event.target.value
    })
  }

  setProblemIndex = (newIndex) => {
    if (newIndex >= 0 && newIndex < this.props.exam.problems.length) {
      this.setState({
        pIndex: newIndex
      })
    }
  }

  prevProblem = () => {
    const newIndex = this.state.pIndex - 1
    this.setProblemIndex(newIndex)
  }
  nextProblem = () => {
    const newIndex = this.state.pIndex + 1
    this.setProblemIndex(newIndex)
  }

  toggleFullPage = (event) => {
    this.setState({
      fullPage: event.target.checked
    })
  }

  getLocationHash = (problem) => {
    var wid = problem.widget
    var hashStr = wid.x + '.' + wid.y + '.' + wid.width + '.' + wid.height
    // Function to calculate hash from a string, from:
    // https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
    var hash = 0
    if (hashStr.length === 0) return hash
    var chr
    for (var i = 0; i < hashStr.length; i++) {
      chr = hashStr.charCodeAt(i)
      hash = ((hash << 5) - hash) + chr
      hash |= 0 // Convert to 32bit integer
    }
    return Math.abs(hash)
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
    const progress = exam.submissions.map(sub => sub.problems[this.state.pIndex])
    const multiple = submission.student && exam.submissions.some(sub =>
      (sub.id !== submission.id && sub.student && sub.student.id === submission.student.id)
    )

    return (
      <div>

        <Hero title='Grade' subtitle='Assign feedback to each solution' />

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                <ProblemSelector problems={exam.problems} changeProblem={this.changeProblem}
                  current={this.state.pIndex} />
                {this.state.editActive
                  ? <EditPanel problemID={problem.id} feedback={this.state.feedbackToEdit}
                    goBack={this.backToFeedback} />
                  : <FeedbackPanel examID={exam.id} submissionID={submission.id}
                    problem={problem} solution={solution} graderID={this.props.graderID}
                    editFeedback={this.editFeedback}
                    updateSubmission={() => {
                      this.props.updateSubmission(this.state.sIndex)
                      this.props.updateExam(this.props.exam.id)
                    }
                    } />
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
                        <SearchBox
                          placeholder='Search for a submission'
                          selected={submission}
                          options={exam.submissions}
                          suggestionKeys={[
                            'student.id',
                            'student.firstName',
                            'student.lastName'
                          ]}
                          setSelected={this.setSubmission}
                          renderSelected={({id, student}) => {
                            if (student) {
                              return `${student.firstName} ${student.lastName} (${student.id})`
                            } else {
                              return `#${id}`
                            }
                          }}
                          renderSuggestion={(submission) => {
                            const stud = submission.student
                            return (
                              <div>
                                <b>{`${stud.firstName} ${stud.lastName}`}</b>
                                <i style={{float: 'right'}}>({stud.id})</i>
                              </div>
                            )
                          }}
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

                <ProgressBar progress={progress} value={'graded_by'} />

                {multiple
                  ? <article className='message is-info'>
                    <div className='message-body'>
                      This student has multiple submissions!
                      Make sure that each applicable feedback option is only selected once.
                    </div>
                  </article> : null
                }

                <p className='box'>
                  <img src={exam.id ? ('api/images/solutions/' + exam.id + '/' +
                    problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) + '?' +
                    this.getLocationHash(problem) : ''} alt='' />
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

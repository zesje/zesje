import React from 'react'
import Notification from 'react-bulma-notification'

import Hero from '../components/Hero.jsx'

import FeedbackPanel from '../components/feedback/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import EditPanel from '../components/feedback/EditPanel.jsx'
import SearchBox from '../components/SearchBox.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'

import * as api from '../api.jsx'

import 'bulma-tooltip/dist/css/bulma-tooltip.min.css'
import './grade/Grade.css'
import '../components/SubmissionNavigation.css'

class Grade extends React.Component {
  state = {
    editActive: false,
    feedbackToEdit: null,
    sIndex: 0,
    pIndex: 0,
    examID: null,
    fullPage: false,
    showTooltips: false
  }

  componentDidMount = () => {
    // If we change the keybindings here we should also remember to
    // update the tooltips for the associated widgets (in render()).
    // Also add the shortcut to ./client/commponents/help/ShortcutsHelp.md
    this.props.bindShortcut(['left', 'h'], this.prev)
    this.props.bindShortcut(['right', 'l'], this.next)
    this.props.bindShortcut(['a'], this.approve)
    this.props.bindShortcut(['shift+left', 'shift+h'], (event) => {
      event.preventDefault()
      this.prevUngraded()
    })
    this.props.bindShortcut(['shift+right', 'shift+l'], (event) => {
      event.preventDefault()
      this.nextUngraded()
    })
    this.props.bindShortcut(['shift+up', 'shift+k'], (event) => {
      event.preventDefault()
      this.prevProblem()
    })
    this.props.bindShortcut(['shift+down', 'shift+j'], (event) => {
      event.preventDefault()
      this.nextProblem()
    })
    this.props.bindShortcut('f', this.toggleFullPage)
    this.props.bindShortcut('ctrl', () => this.setState({showTooltips: true}), 'keydown')
    this.props.bindShortcut('ctrl', () => this.setState({showTooltips: false}), 'keyup')
    let key = 0
    let prefix = ''
    for (let i = 1; i < 21; i++) {
      key = i % 10
      prefix = i > 10 ? 'shift+' : ''
      this.props.bindShortcut(prefix + key, () => this.toggleOption(i - 1))
    }
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

  toggleOption = (index) => {
    const exam = this.props.exam
    const problem = exam.problems[this.state.pIndex]
    if (index + 1 > problem.feedback.length) return

    const optionURI = this.state.examID + '/' +
      exam.submissions[this.state.sIndex].id + '/' +
      problem.id
    api.put('solution/' + optionURI, {
      id: problem.feedback[index].id,
      graderID: this.props.graderID
    })
      .then(result => {
        this.props.updateSubmission(this.state.sIndex)
      })
  }

  approve = () => {
    const exam = this.props.exam
    const problem = exam.problems[this.state.pIndex]
    const optionURI = this.state.examID + '/' +
      exam.submissions[this.state.sIndex].id + '/' +
      problem.id
    api.put('solution/approve/' + optionURI, {
      graderID: this.props.graderID
    })
      .catch(resp => {
        resp.json().then(body => Notification.error('Could not approve feedback: ' + body.message))
      })
      .then(result => {
        this.props.updateSubmission(this.state.sIndex)
      })
  }

  toggleFullPage = () => {
    this.setState({
      fullPage: !this.state.fullPage
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

    const gradedTime = new Date(solution.graded_at)

    return (
      <div>

        <Hero title='Grade' subtitle='Assign feedback to each solution' />

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                <ProblemSelector problems={exam.problems} changeProblem={this.changeProblem}
                  current={this.state.pIndex} showTooltips={this.state.showTooltips} />
                <nav className='panel'>
                  {this.state.editActive
                    ? <EditPanel problemID={problem.id} feedback={this.state.feedbackToEdit}
                      goBack={this.backToFeedback} />
                    : <FeedbackPanel examID={exam.id} submissionID={submission.id}
                      problem={problem} solution={solution} graderID={this.props.graderID}
                      editFeedback={this.editFeedback} showTooltips={this.state.showTooltips}
                      updateSubmission={() => {
                        this.props.updateSubmission(this.state.sIndex)
                      }} grading />
                  }
                </nav>
              </div>

              <div className='column'>
                <div className='level'>
                  <div className='level-item make-wider'>
                    <div className='field has-addons is-mobile'>
                      <div className='control'>
                        <button type='submit'
                          className={'button is-info is-rounded is-hidden-mobile' +
                            (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                          data-tooltip='shift + ←'
                          onClick={this.prevUngraded}>ungraded</button>
                        <button type='submit'
                          className={'button is-link' +
                            (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                          data-tooltip='←'
                          onClick={this.prev}>Previous</button>
                      </div>
                      <div className='control is-wider'>
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
                              <div className='flex-parent'>
                                <b className='flex-child truncated'>
                                  {`${stud.firstName} ${stud.lastName}`}
                                </b>
                                <i className='flex-child fixed'>
                                  ({stud.id})
                                </i>
                              </div>
                            )
                          }}
                        />
                      </div>
                      <div className='control'>
                        <button type='submit'
                          className={'button is-link' +
                            (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                          data-tooltip='→'
                          onClick={this.next}>Next</button>
                        <button type='submit'
                          className={'button is-info is-rounded is-hidden-mobile' +
                            (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                          data-tooltip='shift + →'
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

                <div className='level'>
                  <div className='level-left'>
                    <div className='level-item'>
                      <div>
                        {solution.graded_at
                          ? <div>Graded by: {solution.graded_by.name} <i>({gradedTime.toLocaleString()})</i></div>
                          : <div>Ungraded</div>
                        }
                      </div>
                    </div>
                  </div>
                  <div className='level-right'>
                    <div className='level-item'>
                      <button className={'button is-info is-outlined' + (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                        data-tooltip='f' onClick={this.toggleFullPage}>
                        {this.state.fullPage ? 'Focus problem' : 'View full page'}
                      </button>
                    </div>
                  </div>
                </div>

                <p className={'box' + (solution.graded_at ? ' is-graded' : '')}>
                  <img src={exam.id ? ('api/images/solutions/' + exam.id + '/' +
                    problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) + '?' +
                    this.getLocationHash(problem) : ''} alt='' />
                </p>

              </div>
            </div>
          </div>
        </section>
      </div>
    )
  }
}

export default withShortcuts(Grade)

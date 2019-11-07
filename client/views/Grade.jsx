import React from 'react'
import Notification from 'react-bulma-notification'
import hash from 'object-hash'
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
  /**
   * Constructor sets empty state, and calls updateSubmission.
   * This call will get all metadata and current submission and problem.
   */
  constructor (props) {
    super(props)
    this.state = {}
    this.updateSubmission()
  }

  /**
   * React lifecycle method. Binds all shortcuts.
   */
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
      this.props.bindShortcut(prefix + key, () => this.toggleFeedbackOptionIndex(i - 1))
    }
  }

  /**
   * Navigates the current submission forwards or backwards, and either just to the next, or to the next ungraded.
   * @param direction either 'prev' or 'next'
   * @param ungraded either 'true' or 'false'
   */
  navigate = (direction, ungraded) => {
    api.get(`grade/submissions/${this.props.examID}/${this.state.submission.id}/${this.state.problem.id}` +
      '?direction=' + direction +
      '&grader_id=' + this.props.graderID +
      '&ungraded=' + ungraded).then(sub =>
      this.setState({
        submission: sub
      })
    )
  }
  /**
   * Sugar methods for navigate.
   */
  prev = () => {
    this.navigate('prev', 'false')
  }
  next = () => {
    this.navigate('next', 'false')
  }
  prevUngraded = () => {
    this.navigate('prev', 'true')
  }

  nextUngraded = () => {
    this.navigate('next', 'true')
  }

  /**
   * Updates the grading pages current submission.
   * Also updates the metadata for all other submissions.
   * If no submissionID is specified, defaults to the first submission in the metadata.
   * If no problem is currently in the state, defaults to the first problem in the metadata.
  */
  updateSubmission = (id) => {
    api.get(`grade/metadata/${this.props.examID}`).then(metadata => {
      const examID = metadata.exam_id
      const submissionID = id || metadata.submissions[0].id
      const problemID = this.state.problem ? this.state.problem.id : metadata.problems[0].id
      Promise.all([
        api.get(`submissions/${examID}/${submissionID}`),
        api.get(`problems/${problemID}`)
      ]).then(values => {
        const submission = values[0]
        const problem = values[1]
        this.setState({
          submission: submission,
          problem: problem,
          submissions: metadata.submissions,
          problems: metadata.problems
        })
      })
    })
  }

  /**
   * Updates the current problem to the problem with the passed id.
   * Does not update the metadata, as then the progress bar might update confusingly.
   * @param id the id of the problem to update to.
   */
  updateProblem = (id) => {
    api.get(`problems/${id}`).then(problem => {
      this.setState({
        problem: problem
      })
    })
  }
  /**
   * Finds the index of the current problem and moves to the previous one.
   */
  prevProblem = () => {
    const currentIndex = this.state.problems.findIndex(p => p.id === this.state.problemID) + 1
    const newId = this.state.problems[currentIndex + 1].id
    this.updateProblem(newId)
  }
  /**
   * Finds the index of the current problem and moves to the next one.
   */
  nextProblem = () => {
    const currentIndex = this.state.problems.findIndex(p => p.id === this.state.problemID) + 1
    const newId = this.state.problems[currentIndex - 1].id
    this.updateProblem(newId)
  }
  /**
   * Enter the feedback editing view for a feedback option.
   * todo: move into feedbackpanel.
   * @param feedback the feedback to edit.
   */
  editFeedback = (feedback) => {
    this.setState({
      editActive: true,
      feedbackToEdit: feedback
    })
  }
  /**
   * Go back to all the feedback options.
   * Updates the problem to make sure changes to feedback options are reflected.
   * todo: move into feedbackpanel.
   */
  backToFeedback = () => {
    this.updateProblem(this.state.problem.id)
    this.setState({
      editActive: false
    })
  }

  /**
   * Toggles a feedback option by it's index in the problems list of feedback.
   * @param index the index of the feedback option.
   */
  toggleFeedbackOptionIndex (index) {
    this.toggleFeedbackOption(this.state.problem.feedback[index].id)
  }

  /**
   * Toggles a feedback option.
   * Updates the submission afterwards, to make sure changes are reflected.
   * @param id the id of the feedback option to change.
   */
  toggleFeedbackOption = (id) => {
    const submission = this.state.submission
    const problem = this.state.problem

    api.put(`solution/${this.props.examID}/${submission.id}/${problem.id}`, {
      id: id,
      graderID: this.props.graderID
    }).then(result => {
      this.updateSubmission(submission.id)
    })
  }
  /**
   * Approves the current submission.
   */
  approve = () => {
    const submission = this.state.submission
    const problem = this.state.problem

    api.put(`solution/approve/${this.props.examID}/${submission.id}/${problem.id}`, {
      graderID: this.props.graderID
    }).catch(resp => {
      resp.json().then(body => Notification.error('Could not approve feedback: ' + body.message))
    }).then(result => {
      this.updateSubmission(submission.id)
    })
  }

  /**
   * Toggles full page view.
   */
  toggleFullPage = () => {
    this.setState({
      fullPage: !this.state.fullPage
    })
  }

  /**
   * Hashes the location of the current problems widget.
   * @param problem the problem to hash the widget location for.
   * @returns the hashed string value
   */
  static getLocationHash = (problem) => {
    const wid = problem.widget
    const hashStr = wid.x + '.' + wid.y + '.' + wid.width + '.' + wid.height
    return Grade.hashString(hashStr)
  }

  /**
   * Function to calculate hash from a string, from:
   * https://stackoverflow.com/questions/7616461/generate-a-hash-from-string-in-javascript
   * @param str the string to hash.
   * @returns the hashed string value.
   */
  static hashString = (str) => {
    let hash = 0
    if (str.length === 0) return hash
    let chr
    for (let i = 0; i < str.length; i++) {
      chr = str.charCodeAt(i)
      hash = ((hash << 5) - hash) + chr
      hash |= 0 // Convert to 32bit integer
    }
    return Math.abs(hash)
  }

  render () {
    // Have to not render if no submission exists in the state yet, to prevent crashes.
    // This should only happen while the initial call to update submission in the constructor is still pending.
    if (!this.state.submission) {
      return null
    }
    const examID = this.props.examID
    const graderID = this.props.graderID
    const submission = this.state.submission
    const problem = this.state.problem
    const submissions = this.state.submissions
    const problems = this.state.problems
    const solution = submission.problems.find(p => p.id === problem.id)
    const otherSubmissions = this.state.submissions.filter((sub) => (
      sub.id !== submission.id && submission.student && sub.student && sub.student.id === submission.student.id)
    ).map((sub) => ' #' + sub.id)
    const multiple = otherSubmissions.length > 0
    const anonymous = this.props.gradeAnonymous
    const gradedTime = new Date(solution.graded_at)

    return (
      <div>

        <Hero title='Grade' subtitle='Assign feedback to each solution' />

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                <ProblemSelector
                  problems={problems}
                  setProblemID={this.updateProblem}
                  current={problem}
                  showTooltips={this.state.showTooltips} />
                <nav className='panel'>
                  {this.state.editActive
                    ? <EditPanel
                      problemID={problem.id}
                      feedback={this.state.feedbackToEdit}
                      goBack={this.backToFeedback} />
                    : <FeedbackPanel
                      examID={examID} submissionID={submission.id} graderID={graderID}
                      problem={problem} solution={solution}
                      showTooltips={this.state.showTooltips} grading
                      editFeedback={this.editFeedback}
                      toggleOption={this.toggleFeedbackOption} />
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
                          setSelected={this.updateSubmission}
                          selected={submission}
                          options={submissions}
                          suggestionKeys={(anonymous ? ['id'] : [
                            'student.id',
                            'student.firstName',
                            'student.lastName',
                            'id'
                          ])}
                          renderSelected={({id, student}) => {
                            if (student && !anonymous) {
                              return `${student.firstName} ${student.lastName} (${student.id})`
                            } else {
                              return `#${id}`
                            }
                          }}
                          renderSuggestion={({id, student}) => {
                            if (student && !anonymous) {
                              return (
                                <div className='flex-parent'>
                                  <b className='flex-child truncated'>
                                    {`${student.firstName} ${student.lastName}`}
                                  </b>
                                  <i className='flex-child fixed'>
                                    ({student.id}, #{id})
                                  </i>
                                </div>
                              )
                            } else {
                              return (
                                <div className='flex-parent'>
                                  <b className='flex-child fixed'>
                                    #{id}
                                  </b>
                                </div>
                              )
                            }
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

                <ProgressBar done={problem.n_graded} total={submissions.length} />

                {multiple
                  ? <article className='message is-info'>
                    <div className='message-body'>
                      <p>
                        This student has multiple submissions: (#{submission.id}, {otherSubmissions})
                        Make sure that each applicable feedback option is only selected once.
                      </p>
                    </div>
                  </article>
                  : null
                }

                <div className='level'>
                  <div className='level-left'>
                    <div className='level-item'>
                      <div className={(this.state.showTooltips ? ' tooltip is-tooltip-active is-tooltip-top' : '')}
                        data-tooltip='approve feedback: a' >
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
                  <img src={examID ? ('api/images/solutions/' + examID + '/' +
                    problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) + '?' +
                    Grade.getLocationHash(problem) : ''} alt='' />
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

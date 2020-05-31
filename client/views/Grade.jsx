import React from 'react'
import Notification from 'react-bulma-notification'
import Hero from '../components/Hero.jsx'

import FeedbackPanel from '../components/feedback/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'
import GradeNavigation from './grade/GradeNavigation.jsx'

import * as api from '../api.jsx'

import 'bulma-tooltip/dist/css/bulma-tooltip.min.css'
import './grade/Grade.css'
import '../components/SubmissionNavigation.css'

class Grade extends React.Component {
  /**
   * Constructor sets empty state, and requests metadata for the exam.
   * After getting this metadata, requests and sets the submission and the problem and then syncs
   * the submission with the URL.
   */
  constructor (props) {
    super(props)
    this.state = {}
    api.get(`exams/${this.props.examID}?only_metadata=true` +
        `&shuffle_seed=${this.props.graderID}`).then(metadata => {
      const examID = metadata.exam_id
      const submissionID = this.props.submissionID || metadata.submissions[0].id
      const problemID = this.props.problemID || metadata.problems[0].id
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
          problems: metadata.problems,
          examID: this.props.examID,
          gradeAnonymous: metadata.gradeAnonymous
        }, () => this.props.history.replace('/grade/' + examID + '/' + submissionID + '/' + problemID))
      })
      // eslint-disable-next-line handle-callback-err
    }).catch(err => {
      this.setState({
        submission: null
      })
    })
  }

  /**
   * This method changes the state of the submission and the problem according to the URL.
   * If the submission ID and problem ID is specified in the URL, then it loads the submission corresponding to the URL.
   * If the submission ID and problem ID are missing, it uses the submission from the state (loaded by the constructor)
   * and then replaces the URL to reflect the state.
   * It also sets the submission to null to display error component when unwanted behaviour is observed.
   */
  syncSubmissionWithUrl = () => {
    const UrlIsDifferent = (this.props.problemID !== this.state.problem.id || this.props.submissionID !== this.state.submission.id)
    if (UrlIsDifferent) {
      const submissionID = this.props.submissionID || this.state.submission.id
      const problemID = this.props.problemID || this.state.problem.id
      Promise.all([
        api.get(`submissions/${this.props.examID}/${submissionID}`),
        api.get(`problems/${problemID}`)
      ]).then(values => {
        const submission = values[0]
        const problem = values[1]
        this.setState({
          submission: submission,
          problem: problem
        }, () => this.props.history.replace('/grade/' + this.state.examID + '/' + submission.id + '/' + problem.id))
      }).catch(err => {
        if (err.status === 404) {
          this.setState({
            submission: null
          })
        }
      })
    }
  }

  /**
   * React lifecycle method. Binds all shortcuts.
   */
  componentDidMount = () => {
    // If we change the keybindings here we should also remember to
    // update the tooltips for the associated widgets (in render()).
    // Also add the shortcut to ./client/components/help/ShortcutsHelp.md
    this.props.bindShortcut(['shift+left', 'shift+h'], this.prev)
    this.props.bindShortcut(['shift+right', 'shift+l'], this.next)
    this.props.bindShortcut(['a'], this.toggleApprove)
    this.props.bindShortcut(['left', 'h'], (event) => {
      event.preventDefault()
      this.prevUngraded()
    })
    this.props.bindShortcut(['right', 'l'], (event) => {
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
    this.props.bindShortcut('ctrl', (event) => {
      event.preventDefault()
      this.setState({showTooltips: !this.state.showTooltips})
    })
    let key = 0
    let prefix = ''
    for (let i = 1; i < 21; i++) {
      key = i % 10
      prefix = i > 10 ? 'shift+' : ''
      this.props.bindShortcut(prefix + key, () => this.toggleFeedbackOptionIndex(i - 1))
    }
  }

  /**
   * React lifecycle method. Updates the metadata to keep all submissions and problems up-to-date.
   * @param prevProps - previous properties
   * @param prevState - previous state
   */
  componentDidUpdate = (prevProps, prevState) => {
    const problemID = this.state.problem && String(this.state.problem.id)
    const submissionID = this.state.submission && String(this.state.submission.id)
    if ((prevProps.examID !== this.props.examID && this.props.examID !== this.state.examID) ||
      (prevProps.problemID !== this.props.problemID && this.props.problemID !== problemID) ||
      (prevProps.submissionID !== this.props.submissionID && this.props.submissionID !== submissionID)) {
      this.updateFromUrl()
    }
  }

  /**
   * Navigates the current submission forwards or backwards, and either just to the next, or to the next ungraded.
   * It then pushes the URL of the updated submission to history.
   * Also updates the metadata, and the current problem, to make sure that the
   * progress bar and feedback options are both up to date.
   * @param direction either 'prev' or 'next'
   * @param ungraded either 'true' or 'false'
   */
  navigate = (direction, ungraded) => {
    api.get(`submissions/${this.props.examID}/${this.state.submission.id}` +
      '?problem_id=' + this.state.problem.id +
      '&shuffle_seed=' + this.props.graderID +
      '&direction=' + direction +
      '&ungraded=' + ungraded).then(sub =>
      this.setState({
        submission: sub
      }, () => this.props.history.push('/grade/' + this.props.examID + '/' + this.state.submission.id + '/' + this.state.problem.id))
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
   * Updates the submission from the server, and sets it as the current submission.
  */
  updateSubmission = () => {
    api.get(`submissions/${this.props.examID}/${this.state.submission.id}`).then(sub => {
      this.setState({
        submission: sub
      })
    })
  }

  /**
   * Updates the metadata for the current exam. It then calls syncSubmissionWithUrl to update the submission and problem in the state according to the URL.
   * In case of unwanted behaviour, sets the submission to null for displaying error component.
   */
  updateFromUrl = () => {
    api.get(`exams/${this.props.examID}?only_metadata=true` +
    `&shuffle_seed=${this.props.graderID}`).then(metadata => {
      this.setState({
        submissions: metadata.submissions,
        problems: metadata.problems,
        examID: this.props.examID,
        gradeAnonymous: metadata.gradeAnonymous
      }, () => this.syncSubmissionWithUrl())
      // eslint-disable-next-line handle-callback-err
    }).catch(err => {
      this.setState({
        submission: null
      })
    })
  }

  /**
   * Finds the index of the current problem and moves to the previous one.
   */
  prevProblem = () => {
    const currentIndex = this.state.problems.findIndex(p => p.id === this.state.problem.id)
    if (currentIndex === 0) {
      return
    }
    const newId = this.state.problems[currentIndex - 1].id
    this.navigateProblem(newId)
  }

  /**
   * Finds the index of the current problem and moves to the next one.
   */
  nextProblem = () => {
    const currentIndex = this.state.problems.findIndex(p => p.id === this.state.problem.id)
    if (currentIndex === this.state.problems.length - 1) {
      return
    }
    const newId = this.state.problems[currentIndex + 1].id
    this.navigateProblem(newId)
  }

  /**
   * Navigates the problem to the problem corresponding to the specified problem id by pushing a new URL to history.
   * @param problemID - the id of the problem that we want to navigate to
   */
  navigateProblem = (problemID) => {
    this.props.history.push('/grade/' + this.props.examID + '/' + this.state.submission.id + '/' + problemID)
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
      this.updateSubmission()
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
      this.updateSubmission()
    })
  }

  /**
   * Toggle approve, if a solution is approved it removes the grader,
   * otherwise a grader is added.
   */
   toggleApprove = () => {
     const submission = this.state.submission
     const problem = this.state.problem
     const solution = submission.problems.find(p => p.id === problem.id)

     let graderid = null
     if (solution.graded_by === null) {
       graderid = this.props.graderID
     }

     api.put(`solution/approve/${this.props.examID}/${submission.id}/${problem.id}`, {
       graderID: graderid
     }).catch(resp => {
       resp.json().then(body => {
         Notification.error('Could not ' + (graderid === null ? 'set aside' : 'approve') + ' feedback: ' + body.message)
       })
     }).then(result => {
       this.updateSubmission()
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
    const hero = (<Hero title='Grade' subtitle='Assign feedback to each solution' />)
    const fail = (<Hero title='Oops!' subtitle='Submission does not exist' />)
    // This should happen when there are no submissions or problems for an exam.
    // More specifically, if a user tries to enter a URL for an exam with no submissions.
    // This will also happen while the initial call to update submission in the constructor is still pending.
    if (!this.state.submission) {
      return fail
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
    const gradedTime = new Date(solution.graded_at)
    const gradeAnonymous = this.state.gradeAnonymous

    return (
      <div>

        {hero}

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-fullhd is-one-third-desktop editor-side-panel'>
                <ProblemSelector
                  problems={problems}
                  navigateProblem={this.navigateProblem}
                  current={problem}
                  showTooltips={this.state.showTooltips} />
                <nav className='panel'>
                  <FeedbackPanel
                    examID={examID} submissionID={submission.id} graderID={graderID}
                    problem={problem} solution={solution}
                    showTooltips={this.state.showTooltips} grading
                    setSubmission={this.updateSubmission}
                    toggleOption={this.toggleFeedbackOption}
                    toggleApprove={this.toggleApprove}
                    updateFeedback={this.updateFromUrl} />
                </nav>
              </div>

              <div className='column'>
                <GradeNavigation
                  submission={submission}
                  submissions={submissions}
                  setSubmission={this.updateSubmission}
                  prevUngraded={this.prevUngraded}
                  prev={this.prev}
                  next={this.next}
                  nextUngraded={this.nextUngraded}
                  anonymous={gradeAnonymous}
                  showTooltips={this.state.showTooltips}
                />

                <ProgressBar done={problem.n_graded} total={submissions.length} />

                {multiple
                  ? <article className='message is-info'>
                    <div className='message-body'>
                      <p>
                        This student has possibly submitted multiple copies: (#{submission.id}, {otherSubmissions})
                        Please verify the student identity to bundle these copies before grading.
                      </p>
                    </div>
                  </article>
                  : null
                }

                <div className='level'>
                  <div className='level-left'>
                    <div className='level-item'>
                      {solution.graded_by
                        ? <div>Graded by: {solution.graded_by.name} <i>({gradedTime.toLocaleString()})</i></div>
                        : <div>Ungraded</div>
                      }
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

                <p className={'box is-scrollable-tablet' + (solution.graded_at ? ' is-graded' : '')}>
                  <img
                    src={examID ? ('api/images/solutions/' + examID + '/' +
                      problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) + '?' +
                      Grade.getLocationHash(problem) : ''}
                    alt='' />
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

import React from 'react'
import Notification from 'react-bulma-notification'
import Hero from '../components/Hero.jsx'

import FeedbackPanel from '../components/feedback/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import EditPanel from '../components/feedback/EditPanel.jsx'
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
   * After getting this metadata, requests and sets the submission and the problem.
   */
  constructor (props) {
    super(props)
    this.state = {}
    api.get(`exams/${this.props.examID}?only_metadata=true` +
      `&shuffle_seed=${this.props.graderID}`).then(metadata => {
      const examID = metadata.exam_id
      const submissionID = metadata.submissions[0].id
      const problemID = metadata.problems[0].id
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
   * Navigates the current submission forwards or backwards, and either just to the next, or to the next ungraded.
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
      })
    )
    this.setProblemUpdateMetadata(this.state.problem.id)
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
   * @param id the id of the submission to update to.
  */
  setSubmission = (id) => {
    api.get(`submissions/${this.props.examID}/${id}`).then(sub => {
      this.setState({
        submission: sub
      })
    })
  }
  /**
   * Updates the problem from the server, and sets it as the current problem.
   * Also updates the metadata.
   * @param id the id of the problem to update to.
   */
  setProblemUpdateMetadata = (id) => {
    api.get(`problems/${id}`).then(problem => {
      this.setState({
        problem: problem
      })
    })
    this.updateMetadata()
  }
  /**
   * Updates the metadata for the current exam.
   * This metadata has:
   * id, student for each submission in the exam and
   * id, name for each problem in the exam.
   */
  updateMetadata = () => {
    api.get(`exams/${this.props.examID}?only_metadata=true` +
    `&shuffle_seed=${this.props.graderID}`).then(metadata => {
      this.setState({
        submissions: metadata.submissions,
        problems: metadata.problems
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
    this.setProblemUpdateMetadata(newId)
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
    this.setProblemUpdateMetadata(newId)
  }
  /**
   * Enter the feedback editing view for a feedback option.
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
   */
  backToFeedback = () => {
    this.setProblemUpdateMetadata(this.state.problem.id)
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
      this.setSubmission(submission.id)
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
      this.setSubmission(submission.id)
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
       this.setSubmission(submission.id)
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
    // Have to not render if no submission exists in the state yet, to prevent crashes.
    // This should only happen while the initial call to update submission in the constructor is still pending.
    if (!this.state.submission) {
      return hero
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

    return (
      <div>

        {hero}

        <section className='section'>

          <div className='container'>
            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                <ProblemSelector
                  problems={problems}
                  setProblemUpdateMetadata={this.setProblemUpdateMetadata}
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
                      setSubmission={this.setSubmission}
                      editFeedback={this.editFeedback}
                      toggleOption={this.toggleFeedbackOption}
                      toggleApprove={this.toggleApprove} />
                  }
                </nav>
              </div>

              <div className='column'>
                <GradeNavigation
                  submission={submission}
                  submissions={submissions}
                  setSubmission={this.setSubmission}
                  prevUngraded={this.prevUngraded}
                  prev={this.prev}
                  next={this.next}
                  nextUngraded={this.nextUngraded}
                  anonymous={this.props.gradeAnonymous}
                  showTooltips={this.state.showTooltips}
                />

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

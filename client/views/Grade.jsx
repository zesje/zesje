import React from 'react'
import Notification from 'react-bulma-notification'
import Hero from '../components/Hero.jsx'
import Fail from './Fail.jsx'
import update from 'immutability-helper'

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
   * After getting this metadata, if the submissionID is provided in the URL, loads the submission according to the submissionID,
   * else loads the first submission from the metadata and then replaces the URL to match the submission.
   */
  constructor (props) {
    super(props)
    this.state = {}
  }

  setStateAsync = (state) => new Promise((resolve, reject) => {
    this.setState(state, resolve)
  })

  init = async () => {
    await this.setStateAsync({feedbackFilters: {}, gradedBy: -1})
    await this.setStateAsync({hasFilters: this.hasFilters()})

    try {
      const metadata = await api.get(`exams/${this.props.examID}?only_metadata=true&shuffle_seed=${this.props.graderID}`)
      const partialState = {
        submissions: metadata.submissions,
        problems: metadata.problems,
        isUnstructured: metadata.layout === 'unstructured',
        examID: this.props.examID,
        gradeAnonymous: metadata.gradeAnonymous
      }

      const examID = metadata.exam_id
      const submissionID = this.props.submissionID || metadata.submissions[0].id
      const problemID = this.props.problemID || metadata.problems[0].id
      try {
        const values = await Promise.all([
          api.get(`submissions/${examID}/${submissionID}?${[
            `problem_id=${problemID}`,
            ...this.getFilterArguments()
          ].join('&')}`),
          api.get(`problems/${problemID}`),
          api.get(`graders`)
        ])

        const submission = values[0]
        const problem = values[1]
        const graders = values[2]
        await this.setStateAsync({
          submission: submission.submission,
          problem: problem,
          graders: graders,
          matchingResults: submission.filter_matches,
          ...partialState
        }, () => this.props.history.replace(this.getURL(submissionID, problemID)))
      } catch (err) {
        await this.setStateAsync({
          submission: null,
          problem: null,
          ...partialState
        })
      }
    } catch (err) {
      await this.setStateAsync({
        submission: null
      })
    }
  }

  /**
   * This method changes the state of the submission and the problem according to the URL. This method is called once the latest metadata is fetched from the backend.
   * If the submission ID is specified in the URL, then it loads the submission corresponding to the URL.
   * If it is missing, it loads the first submission from the metadata and then replaces the URL to reflect the state.
   * It also sets the submission to null to display error component when unwanted behaviour is observed.
   */
  syncSubmissionWithUrl = () => {
    const UrlIsDifferent = (!this.state.problem || !this.state.submission ||
      this.props.problemID !== this.state.problem.id || this.props.submissionID !== this.state.submission.id)
    if (UrlIsDifferent) {
      const submissionID = this.props.submissionID || this.state.submissions[0].id
      const problemID = this.props.problemID || this.state.problems[0].id
      Promise.all([
        api.get(`submissions/${this.props.examID}/${submissionID}?${
          [
            `problem_id=${problemID}`,
            ...this.getFilterArguments()
          ].join('&')
        }`),
        api.get(`problems/${problemID}`)
      ]).then(values => {
        const submission = values[0]
        const problem = values[1]
        this.setState({
          submission: submission.submission,
          problem: problem,
          matchingResults: submission.filter_matches
        }, () => {
          this.props.history.replace(this.getURL(submission.submission.id, problem.id))
        })
      }).catch(err => {
        if (err.status === 404) {
          this.setState({
            submission: null,
            problem: null
          })
        }
      })
    }
  }

  /**
   * React lifecycle method. Binds all shortcuts.
   */
  componentDidMount = async () => {
    await this.init()
    // If we change the keybindings here we should also remember to
    // update the tooltips for the associated widgets (in render()).
    // Also add the shortcut to ./client/components/help/ShortcutsHelp.md
    this.props.bindShortcut(['shift+left', 'shift+h'], this.first)
    this.props.bindShortcut(['shift+right', 'shift+l'], this.last)
    this.props.bindShortcut(['a'], this.toggleApprove)
    this.props.bindShortcut(['left', 'h'], (event) => {
      event.preventDefault()
      this.prev()
    })
    this.props.bindShortcut(['right', 'l'], (event) => {
      event.preventDefault()
      this.next()
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
      (prevProps.problemID !== this.props.problemID && (!problemID || this.props.problemID !== problemID)) ||
      (prevProps.submissionID !== this.props.submissionID && (!submissionID || this.props.submissionID !== submissionID))) {
      // The URL has changed and at least one of exam metadata, problem or submission does not match the URL
      // or the URL has changed and submission or problem is not defined
      this.updateFromUrl()
    }
  }

  getURL = (submissionID, problemID) => {
    return `${this.props.parentURL}/grade/${submissionID}/${problemID}`
  }

  /**
   * Navigates the current submission forwards or backwards, and either just to the next, or to the next ungraded.
   * It then pushes the URL of the updated submission to history.
   * Also updates the metadata, and the current problem, to make sure that the
   * progress bar and feedback options are both up to date.
   * @param direction either 'prev', 'next', 'first' or 'last'
   */
  navigate = async (direction) => {
    const fb = (await api.get(`feedback/${this.state.problem.id}`)).map(fb => fb.id)

    this.setState({
      feedbackFilters: Object.entries(this.state.feedbackFilters).filter(
        option => fb.includes(parseInt(option[0]))
      )
        .reduce(
          (previous, current) => ({...previous, [parseInt(current[0])]: current[1]}), {})
    })

    const {submission, filter_matches: matchingResults} = await api.get(
      `submissions/${this.props.examID}/${this.state.submission.id}?${[
        `problem_id=${this.state.problem.id}`,
        `shuffle_seed=${this.props.graderID}`,
        `direction=${direction}`,
        ...this.getFilterArguments()
      ].join('&')}`
    )
    this.setState({
      submission,
      matchingResults
    }, () => {
      this.props.history.push(this.getURL(this.state.submission.id, this.state.problem.id))
    })
  }
  /**
   * Sugar methods for navigate.
   */
  prev = () => {
    this.navigate('prev')
  }
  next = () => {
    this.navigate('next')
  }
  first = () => {
    this.navigate('first')
  }
  last = () => {
    this.navigate('last')
  }

  getFilterArguments = () => {
    const filterArguments = [
      `ungraded=${(this.state.gradedBy === -1).toString()}`,
      ...Object.entries(this.state.feedbackFilters)
        .filter(entry => entry[1] !== 'no_filter')
        .map(entry => `${entry[1]}_feedback=${entry[0]}`)
    ]
    if (this.state.gradedBy >= 1) {
      filterArguments.push(`graded_by=${this.state.gradedBy}`)
    }
    return filterArguments
  }

  /**
   * Updates the submission from the server, and sets it as the current submission.
  */
  updateSubmission = async () => {
    const data = await api.get(`submissions/${this.props.examID}/${this.state.submission.id}?${[
      `problem_id=${this.state.problem.id}`,
      ...this.getFilterArguments()
    ].join('&')}`)

    this.setState(prevState => ({
      submission: data.submission,
      matchingResults: data.filter_matches,
      problem: update(prevState.problem, {
        n_graded: {
          $set: data.n_graded
        }
      }),
      hasFilters: this.hasFilters()
    }))
  }

  hasFilters = () => {
    return Object.keys(this.state.feedbackFilters).length > 0 || this.state.gradedBy !== -1
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
        submission: null,
        problem: null
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
   * Navigates to the given problem by pushing a new URL to history without changing the submission.
   * @param problemID - the id of the problem that we want to navigate to
   */
  navigateProblem = (problemID) => {
    this.props.history.push(this.getURL(this.state.submission.id, problemID))
  }

  /**
   * Navigates to the given submission by pushing a new URL to history without changing the problem.
   * @param submissionID - the id of the submission that we want to navigate to
   */
  navigateSubmission = (submissionID) => {
    this.props.history.push(this.getURL(submissionID, this.props.problemID))
  }

  /**
   * Toggles a feedback option by it's index in the problems list of feedback.
   * @param index the index of the feedback option.
   */
  toggleFeedbackOptionIndex = (index) => {
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

  applyGraderFilter = (graderId) => {
    this.setState({gradedBy: graderId}, () => {
      this.updateSubmission()
    })
  }

  applyFilter = (e, id, newFilterMode) => {
    e.stopPropagation()
    this.setState(oldState => {
      newFilterMode = oldState.feedbackFilters[id] === newFilterMode ? 'no_filter' : newFilterMode
      if (newFilterMode === 'no_filter') {
        const clone = {
          feedbackFilters: {
            ...oldState.feedbackFilters
          }
        }
        delete clone.feedbackFilters[id]
        return clone
      } else {
        return {
          feedbackFilters: {
            ...oldState.feedbackFilters,
            [id]: newFilterMode
          }
        }
      }
    }, () => {
      this.updateSubmission()
    })
  }

  clearFilters = () => {
    const selectFilterBy = document.getElementById('filter_graded_by')
    selectFilterBy.selectedIndex = 0
    this.applyGraderFilter(parseInt(selectFilterBy.value))
    this.setState({ feedbackFilters: {} }, () => {
      this.updateSubmission()
    })
  }

  render () {
    const hero = (<Hero title='Grade' subtitle='Assign feedback to each solution' />)
    // This should happen when there are no submissions or problems for an exam.
    // More specifically, if a user tries to enter a URL for an exam with no submissions.
    // This will also happen while the initial call to update submission in the constructor is still pending.
    if (this.state.submission === undefined) {
      // submission is being loaded, we just want to show a loading screen
      return hero
    }

    if (this.state.submission === null) {
      // no stats, show the error message
      const message = ((this.state.submissions && this.state.submissions.length > 0)
        ? 'Submission does not exist' : 'There are no submissions yet')
      return <Fail message={message} />
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
              <div className='column is-one-quarter-fullhd is-one-third-desktop'>
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
                    feedbackFilters={this.state.feedbackFilters}
                    applyFilter={this.applyFilter}
                    updateFeedback={this.updateFromUrl}
                  />
                </nav>
              </div>

              <div className='column'>
                <div style={{display: 'grid', gridTemplateColumns: '5fr 1.8fr 2fr', gap: '1em'}}>
                  <GradeNavigation
                    submission={submission}
                    submissions={submissions}
                    setSubmission={this.navigateSubmission}
                    first={this.first}
                    prev={this.prev}
                    next={this.next}
                    last={this.last}
                    anonymous={gradeAnonymous}
                    showTooltips={this.state.showTooltips}
                  />

                  <div className='select is-link is-normal'>
                    <select
                      id='filter_graded_by'
                      style={{width: '100%'}}
                      value={this.state.gradedBy}
                      onChange={(e) => this.applyGraderFilter(parseInt(e.target.value))}
                    >
                      <option value='-1' key='-1'>Ungraded</option>
                      <option value='0' key='0'>All</option>
                      {this.state.graders.map((grader) =>
                        <option value={grader.id} key={grader.id}>
                          {grader.oauth_id}
                        </option>
                      )}
                    </select>
                  </div>

                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr max-content',
                    gap: '0.5em',
                    justifyItems: 'end',
                    height: 'max-content',
                    alignItems: 'center'
                  }}>
                    {this.state.matchingResults} matching solutions
                    <button
                      className='button is-danger'
                      style={{width: 'max-content'}}
                      onClick={this.clearFilters}
                      disabled={!this.state.hasFilters}
                    >
                      <span className='icon is-medium'>
                        <i
                          className='fa fa-lg fa-filter'
                          style={{transform: 'translateX(-17%)'}}
                        />
                        <span
                          className='icon is-small'
                          style={{position: 'absolute', right: '12%', bottom: 0}}
                        >
                          <i className='fa fa-times' />
                        </span>
                      </span>
                    </button>
                  </div>
                </div>
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
                      {solution.graded_by ? <div>Graded by: {(solution.graded_by.name ? solution.graded_by.name + ' - ' : '') + solution.graded_by.oauth_id} <i>({gradedTime.toLocaleString()})</i></div>
                        : <div>Ungraded</div>
                      }
                    </div>

                  </div>

                  <div className='level-right'>
                    <div className='level-item'>
                      {!this.state.isUnstructured &&
                        <button className={'button is-info is-outlined' + (this.state.showTooltips ? ' tooltip is-tooltip-active' : '')}
                          data-tooltip='f' onClick={this.toggleFullPage}>
                          {this.state.fullPage ? 'Focus problem' : 'View full page'}
                        </button>
                      }
                    </div>
                  </div>
                </div>

                <p className={'box is-scrollable-desktop is-scrollable-tablet' +
                  (solution.graded_at ? ' is-graded' : '')}>
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

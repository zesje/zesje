import React from 'react'
import { toast } from 'bulma-toast'
import Hero from '../components/Hero.jsx'
import Fail from './Fail.jsx'
import update from 'immutability-helper'

import FeedbackPanel from '../components/feedback/FeedbackPanel.jsx'
import ProblemSelector from './grade/ProblemSelector.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'
import withRouter from '../components/RouterBinder.jsx'
import GradeNavigation from './grade/GradeNavigation.jsx'
import { indexFeedbackOptions, findFeedbackByIndex } from '../components/feedback/FeedbackUtils.jsx'

import * as api from '../api.jsx'

import './grade/Grade.css'
import '../components/SubmissionNavigation.css'

const defaultGraderFilter = -1

const FiltersInfo = ({ hasFilters, matchingResults, clearFilters }) => {
  const text = matchingResults +
    (hasFilters ? ' matching ' : ' ') +
    (matchingResults === 1 ? 'solution' : 'solutions')

  return (
    <div className='column' style={{
      display: 'grid',
      gridTemplateColumns: '1fr max-content',
      gap: '0.5em',
      justifyItems: 'end',
      height: 'max-content',
      alignItems: 'center'
    }}>
      {text}
      <button
        className='button is-danger'
        onClick={clearFilters}
        disabled={!hasFilters}
      >
        <span className='icon is-medium'>
          <i
            className='fa fa-lg fa-filter'
            style={{ transform: 'translateX(-17%)' }}
          />
          <span
            className='icon is-small'
            style={{ position: 'absolute', right: '12%', bottom: 0 }}
          >
            <i className='fa fa-times' />
          </span>
        </span>
      </button>
    </div>
  )
}

class Grade extends React.Component {
  /**
   * Constructor sets empty state, and requests metadata for the exam.
   * After getting this metadata, if the submissionID is provided in the URL,
   * loads the submission according to the submissionID,
   * else loads the first submission from the metadata and then replaces the URL to match the submission.
   */
  constructor (props) {
    super(props)
    this.state = { feedbackFilters: {}, gradedBy: defaultGraderFilter }
    this.state = { ...this.state, hasFilters: this.hasFilters() }

    Promise.all([
      api.get(`exams/${this.props.examID}?only_metadata=true`),
      api.get('graders')
    ]).then(([metadata, graders]) => {
      const partialState = {
        submissions: metadata.submissions,
        problems: metadata.problems,
        isUnstructured: metadata.layout === 'unstructured',
        examID: props.examID,
        gradeAnonymous: metadata.gradeAnonymous,
        graders: graders
      }

      const examID = metadata.exam_id
      if (!(metadata.submissions.length && metadata.problems.length)) {
        this.setState({
          submission: null,
          problem: null,
          ...partialState
        })
      } else {
        const submissionID = this.props.router.params.submissionID || metadata.submissions[0].id
        const problemID = this.props.router.params.problemID || metadata.problems[0].id

        Promise.all([
          api.get(`submissions/${examID}/${submissionID}?${[
            `problem_id=${problemID}`, ...this.getFilterArguments()].join('&')}`),
          api.get(`problems/${problemID}`)
        ]).then(([submission, problem]) => {
          this.setState({
            submission: submission,
            problem: problem,
            matchingResults: submission.meta.filter_matches,
            ...partialState
          }, () => this.props.router.navigate(this.getURL(submissionID, problemID)), { replace: true })
        }).catch(err => {
          console.log(err)
          this.setState({
            submission: null,
            problem: null,
            ...partialState
          })
        })
      }
    }).catch(err => {
      console.log(err)
      this.setState({
        submissions: null,
        problems: null,
        graders: null,
        examID: props.examID
      })
    })
  }

  /**
   * This method changes the state of the submission and the problem according to the URL.
   * This method is called once the latest metadata is fetched from the backend.
   * If the submission ID is specified in the URL, then it loads the submission corresponding to the URL.
   * If it is missing, it loads the first submission from the metadata and then replaces the URL to reflect the state.
   * It also sets the submission to null to display error component when unwanted behaviour is observed.
   */
  syncSubmission = () => {
    if (!(this.state.submissions.length && this.state.problems.length)) return

    const submissionID = this.props.router.params.submissionID || this.state.submissions[0].id
    const problemID = this.props.router.params.problemID || this.state.problems[0].id
    Promise.all([
      api.get(`submissions/${this.props.examID}/${submissionID}?${
        [`problem_id=${problemID}`, ...this.getFilterArguments()].join('&')}`),
      api.get(`problems/${problemID}`)
    ]).then(values => {
      const submission = values[0]
      const problem = values[1]
      this.setState({
        submission: submission,
        problem: problem,
        matchingResults: submission.meta.filter_matches
      }, () => {
        this.props.router.navigate(this.getURL(submission.id, problem.id), { replace: true })
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

  /**
   * React lifecycle method. Binds all shortcuts.
   */
  componentDidMount = () => {
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
      this.setState({ showTooltips: !this.state.showTooltips })
    })
    let key = 0
    let prefix = ''
    for (let i = 1; i < 21; i++) {
      key = i % 10
      prefix = i > 10 ? 'shift+' : ''
      this.props.bindShortcut(prefix + key, () => this.toggleFeedbackOptionIndex(i))
    }
  }

  /**
   * React lifecycle method. Updates the metadata to keep all submissions and problems up-to-date.
   * @param prevProps - previous properties
   * @param prevState - previous state
   */
  componentDidUpdate = (prevProps, prevState) => {
    const { problemID, submissionID } = this.props.router.params

    const hasProblem = this.state.problem && this.state.problem.id > 0
    const hasSubmission = this.state.submission && this.state.submission.id > 0
    if ((prevProps.examID !== this.props.examID && this.props.examID !== this.state.examID) ||
      (prevProps.router.params.problemID !== problemID &&
        (!hasProblem || problemID !== this.state.problem.id)) ||
      (prevProps.router.params.submissionID !== submissionID &&
        (!hasSubmission || submissionID !== this.state.submission.id))) {
      // The URL has changed and at least one of exam metadata, problem or submission does not match the URL
      // or the URL has changed and submission or problem is not defined
      this.setState({
        problemID, submissionID
      }, this.updateFromUrl)
    }
  }

  getURL = (submissionID, problemID) => {
    return `/exams/${this.props.examID}/grade/${submissionID}/${problemID}`
  }

  /**
   * Navigates the current submission forwards or backwards, and either just to the next, or to the next ungraded.
   * It then pushes the URL of the updated submission to history.
   * Also updates the metadata, and the current problem, to make sure that the
   * progress bar and feedback options are both up to date.
   * @param direction either 'prev', 'next', 'first' or 'last'
   */
  navigate = async (direction) => {
    const fb = Object.keys(this.state.problem.feedback)

    this.setState({
      feedbackFilters: Object.entries(this.state.feedbackFilters).reduce(
        (previous, option) => fb.includes(option[0]) ? { ...previous, [parseInt(option[0])]: option[1] } : previous,
        {}
      )
    })

    const submission = await api.get(
      `submissions/${this.props.examID}/${this.state.submission.id}?${[
        `problem_id=${this.state.problem.id}`,
        `direction=${direction}`,
        ...this.getFilterArguments()
      ].join('&')}`
    )

    this.setState({
      submission,
      matchingResults: submission.meta.filter_matches
    }, () => {
      this.props.router.navigate(this.getURL(this.state.submission.id, this.state.problem.id))
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
    const submission = await api.get(`submissions/${this.props.examID}/${this.state.submission.id}?${[
      `problem_id=${this.state.problem.id}`,
      ...this.getFilterArguments()
    ].join('&')}`)

    this.setState(prevState => ({
      submission,
      matchingResults: submission.meta.filter_matches,
      problem: update(prevState.problem, {
        n_graded: {
          $set: submission.meta.n_graded
        }
      }),
      hasFilters: this.hasFilters()
    }))
  }

  hasFilters = () => {
    return Object.keys(this.state.feedbackFilters).length > 0 || this.state.gradedBy !== defaultGraderFilter
  }

  /**
   * Updates the metadata for the current exam.
   * It then calls syncSubmission to update the submission and problem in the state according to the URL.
   * In case of unwanted behaviour, sets the submission to null for displaying error component.
   */
  updateFromUrl = () => {
    api.get(`exams/${this.props.examID}?only_metadata=true`).then(metadata => {
      this.setState({
        submissions: metadata.submissions,
        problems: metadata.problems,
        examID: this.props.examID,
        gradeAnonymous: metadata.gradeAnonymous
      }, this.syncSubmission)
      // eslint-disable-next-line handle-callback-err
    }).catch(err => {
      console.log(err)
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
    this.props.router.navigate(this.getURL(this.state.submission.id, problemID))
  }

  /**
   * Navigates to the given submission by pushing a new URL to history without changing the problem.
   * @param submissionID - the id of the submission that we want to navigate to
   */
  navigateSubmission = (submissionID) => {
    this.props.router.navigate(this.getURL(submissionID, this.props.router.params.problemID))
  }

  /**
   * Toggles a feedback option by it's index in the problems list of feedback.
   * @param index the index of the feedback option.
   */
  toggleFeedbackOptionIndex = (index) => {
    const feedback = indexFeedbackOptions(this.state.problem.feedback, this.state.problem.root_feedback_id)
    const fb = findFeedbackByIndex(feedback, index)
    if (fb.parent === null) {
      return null
    }
    this.toggleFeedbackOption(fb.id)
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
      id: id
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
     const solution = submission.problems.find(p => p.problemId === problem.id)

     const approve = solution.gradedBy === null

     api.put(`solution/approve/${this.props.examID}/${submission.id}/${problem.id}`, {
       approve: approve
     }).catch(resp => {
       resp.json().then(body => {
         toast({
           message: 'Could not ' + (approve ? 'set aside' : 'approve') + ' feedback: ' + body.message,
           type: 'is-danger'
         })
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
      hash = ((hash << 5) - hash) + chr // eslint-disable-line no-bitwise
      // Convert to 32bit integer
      hash |= 0 // eslint-disable-line no-bitwise
    }
    return Math.abs(hash)
  }

  applyGraderFilter = (graderId) => {
    this.setState({ gradedBy: graderId }, () => {
      this.updateSubmission()
    })
  }

  applyFeedbackFilter = (e, id, newFilterMode) => {
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
        if (Object.keys(clone.feedbackFilters).length === 0) {
          clone.gradedBy = -1
        }
        return clone
      } else {
        return {
          feedbackFilters: {
            ...oldState.feedbackFilters,
            [id]: newFilterMode
          },
          gradedBy: oldState.gradedBy === -1 ? 0 : oldState.gradedBy
        }
      }
    }, () => {
      this.updateSubmission()
    })
  }

  clearFilters = () => {
    this.setState({ feedbackFilters: {}, gradedBy: defaultGraderFilter }, () => {
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

    if (!this.state.problems || this.state.problems.length === 0) {
      return <Fail message='No problems defined in the exam' />
    }

    if (this.state.submission === null) {
      // no stats, show the error message
      const message = ((this.state.submissions && this.state.submissions.length > 0)
        ? 'Submission does not exist'
        : 'There are no submissions yet')
      return <Fail message={message} />
    }

    const examID = this.props.examID
    const submission = this.state.submission
    const problem = this.state.problem
    const submissions = this.state.submissions
    const problems = this.state.problems
    const solution = submission.problems.find(p => p.problemId === problem.id)
    const otherSubmissions = this.state.submissions.filter((sub) => (
      sub.id !== submission.id && submission.student && sub.student && sub.student.id === submission.student.id)
    ).map((sub) => ' #' + sub.id)
    const multiple = otherSubmissions.length > 0
    const gradedTime = new Date(solution.gradedAt)
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
                  showTooltips={this.state.showTooltips}
                />
                <nav className='panel is-sticky has-modal'>
                  <FeedbackPanel
                    examID={examID} submissionID={submission.id}
                    problem={problem} solution={solution}
                    showTooltips={this.state.showTooltips}
                    setSubmission={this.updateSubmission}
                    toggleOption={this.toggleFeedbackOption}
                    toggleApprove={this.toggleApprove}
                    feedbackFilters={this.state.feedbackFilters}
                    applyFilter={this.applyFeedbackFilter}
                    updateFeedback={this.syncSubmission}
                  />
                </nav>
              </div>

              <div className='column'>
                <div className='columns is-multiline is-mobile'>
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
                  <div className='column is-one-quarter-desktop is-half-mobile'>
                    <div className='control has-icons-left'>
                      <div className='select is-link is-fullwidth'>
                        <select
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
                      <span className='icon is-small is-left'>
                        <i className='fa fa-filter' />
                      </span>
                    </div>
                  </div>
                  <FiltersInfo
                    hasFilters={this.state.hasFilters}
                    matchingResults={this.state.matchingResults}
                    clearFilters={this.clearFilters}
                  />
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
                  : null}

                <div className='level'>
                  <div className='level-left'>

                    <div className='level-item'>
                      {solution.gradedBy
                        ? <div>
                          Graded by: {(solution.gradedBy.name ? solution.gradedBy.name + ' - ' : '') +
                          solution.gradedBy.oauth_id} <i>({gradedTime.toLocaleString()})</i>
                        </div>
                        : <div>Ungraded</div>}
                    </div>

                  </div>

                  <div className='level-right'>
                    <div className='level-item'>
                      {!this.state.isUnstructured &&
                        <button
                          className={'button is-info is-outlined has-tooltip-arrow' +
                            (this.state.showTooltips ? ' has-tooltip-active' : '')}
                          data-tooltip='f' onClick={this.toggleFullPage}
                        >
                          {this.state.fullPage ? 'Focus problem' : 'View full page'}
                        </button>}
                    </div>
                  </div>
                </div>

                <p className={'box is-sticky is-scrollable-desktop is-scrollable-tablet' +
                  (solution.gradedAt ? ' is-graded' : '')}
                >
                  <img
                    src={examID
                      ? ('api/images/solutions/' + examID + '/' +
                        problem.id + '/' + submission.id + '/' + (this.state.fullPage ? '1' : '0')) + '?' +
                        Grade.getLocationHash(problem)
                      : ''}
                    alt=''
                  />
                </p>
              </div>
            </div>
          </div>
        </section>
      </div>
    )
  }
}

export default withRouter(withShortcuts(Grade))

import React from 'react'
import 'bulma-tooltip/dist/css/bulma-tooltip.min.css'

import humanizeDuration from 'humanize-duration'
import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'

const Tooltip = (props) => {
  if (!props.text) {
    return null
  }

  let tooltipClass = 'icon tooltip is-tooltip-right '
  if (props.text.length > 100) {
    tooltipClass += 'is-tooltip-multiline '
  }

  return (
    <span
      className={tooltipClass}
      data-tooltip={props.text}
    >
      <i className='fa fa-comment' />
    </span>
  )
}

const formatTime = (seconds) => {
  // returns human readable string showing the elapsed time
  const formatTimePrecision = (seconds, precision) => (
    humanizeDuration(1000 * Math.round(seconds / precision) * precision, { delimiter: ' and ' }) 
  )

  if (seconds > 3600) { // Use 10 minute precision
    return formatTimePrecision(seconds, 600)
  } else if (seconds > 600) { // Use minute precision
    return formatTimePrecision(seconds, 60)
  } else if (seconds > 30) { // Use 10 second precision
    return formatTimePrecision(seconds, 10)
  } else if (seconds >= 5) { // Use 5 second precision
    return formatTimePrecision(seconds, 5)
  } else {
    return 'a few seconds'
  }
}

const ProblemSummary = (props) => (
  <React.Fragment>
    <h3 className='has-text-centered'>
      {/^\d/.test(props.problem.name) ? 'Problem ' : null}
      {props.problem.name}
    </h3>
    <table className='table is-striped'>
      <thead>
        <tr>
          <th> Feedback </th>
          <th> Score </th>
          <th> #&nbsp;Assigned</th>
        </tr>
      </thead>
      <tbody>
        {
          props.problem.feedback.map((option, i) => {
            return <tr key={i}>
              <td>
                {option.name}
                <Tooltip text={option.description} />
              </td>
              <td> {option.score} </td>
              <td> {option.used} </td>
            </tr>
          })
        }
      </tbody>
    </table>
    <ul>
      {props.graders
        ? props.graders.graders.map((grader, i) => {
          if (grader.name === 'Zesje') return ''
          return <li key={i}>
            {grader.graded + ' ' + (grader.graded > 1 ? 'solutions ' : 'solution ')}
            graded by {grader.name}
            {grader.total_time > 0
              ? ' in ' + formatTime(grader.total_time) +
                (grader.graded > 1
                  ? ' (' + formatTime(grader.avg_grading_time) + ' per solution)'
                  : '')
              : ''}.
          </li>
        })
        : ''
      }
    </ul>
  </React.Fragment>
)

class Overview extends React.Component {
  state = {
    graderStatistics: null,
    statsLoaded: false
  }

  constructor (props) {
    super(props)
    this.state = {
      graderStatistics: null
    }
  }

  componentWillMount () {
    api.get(`export/graders/${this.props.exam.id}`)
      .then(stats => {
        this.setState({
          graderStatistics: stats,
          statsLoaded: true
        })
      })
  }

  render () {
    return (
      <div>

        <Hero title='Overview' subtitle='Analyse the exam results' />

        <h1 className='is-size-1 has-text-centered'>Exam "{this.props.exam.name}" </h1>

        <section className='column is-half is-offset-3'>
          <h3 className='subtitle is-size-3 has-text-centered'> At a glance </h3>
          <figure className='image is-4by3'>
            <img src={'api/images/summary/' + this.props.exam.id} />
          </figure>
        </section>

        <section>
          <h3 className='title is-size-3 has-text-centered'> Problem Details </h3>
          <div className='columns is-tablet is-multiline'>
            { this.props.exam.problems.map((problem, i) => (
              <div className='column is-one-half-tablet is-one-third-desktop' key={i}>
                <div className='content'>
                  <ProblemSummary problem={problem}
                    graders={this.state.statsLoaded ? this.state.graderStatistics.problems[i] : null} />
                </div>
              </div>
            ))
            }
          </div>
        </section>
      </div >
    )
  }
}

export default Overview

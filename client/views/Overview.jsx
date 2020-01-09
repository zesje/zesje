import React from 'react'
import 'bulma-tooltip/dist/css/bulma-tooltip.min.css'

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
  </React.Fragment>
)

const displayGradingTime = (time) => {
  if (time > 59) {
    return `${Math.floor(time / 60)}min ${(time % 60)}s`
  } else {
    return `${time}s`
  }
}

const GradersSummary = (props) => (
  <React.Fragment>
    <h3 className='has-text-centered'>
      {/^\d/.test(props.problem.name) ? 'Problem ' : null}
      {props.problem.name}
    </h3>
    <table className='table is-striped'>
      <thead>
        <tr>
          <th> Name </th>
          <th> #&nbsp;Graded </th>
          <th> Avg. Score </th>
          <th> #&nbsp;Max/Min Grade </th>
          <th> Avg. Grading Time </th>
        </tr>
      </thead>
      <tbody>
        {
          props.problem.graders.map((grader, i) => {
            return <tr key={i}>
              <td> {grader.name} </td>
              <td> {grader.graded} </td>
              <td> {Math.round(grader.avg_score * 100) / 100} </td>
              <td> {grader.max_score} / {grader.min_score} </td>
              <td> {displayGradingTime(grader.avg_grading_time)} </td>
            </tr>
          })
        }
      </tbody>
    </table>
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
            {
              this.props.exam.problems.map((problem, i) => (
                <div className='column is-one-half-tablet is-one-third-desktop' key={i}>
                  <div className='content'>
                    <ProblemSummary problem={problem} />
                  </div>
                </div>
              ))
            }
          </div>
        </section>

        <section>
          <h3 className='title is-size-3 has-text-centered'> Grader Details </h3>
          { this.state.statsLoaded &&
              this.state.graderStatistics.problems.map((problem, i) => (
                <div className='content' key={i}>
                  <GradersSummary problem={problem} />
                </div>
              ))
          }
        </section>

      </div >
    )
  }
}

export default Overview

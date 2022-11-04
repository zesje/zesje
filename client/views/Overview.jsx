import React from 'react'

import Plotly from 'plotly.js-cartesian-dist-min'
import createPlotlyComponent from 'react-plotly.js/factory'

import { range, exp, sqrt, pow, pi } from 'mathjs'

import humanizeDuration from 'humanize-duration'
import Fail from './Fail.jsx'
import Loading from './Loading.jsx'
import * as api from '../api.jsx'

const Plot = createPlotlyComponent(Plotly)

const Tooltip = (props) => {
  if (!props.text) {
    return null
  }

  let tooltipClass = 'icon tooltip has-tooltip-right '
  if (props.text.length > 100) {
    tooltipClass += 'has-tooltip-multiline '
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

const GraderDetails = (props) => {
  if (!props.graders.length && props.autograded === 0) {
    return (
      <article className='message is-danger'>
        <div className='message-body'>
          No solutions have been graded for this problem.
        </div>
      </article>
    )
  }

  return (
    <>
      <h3 className='is-size-5'> Grader details </h3>
      {props.graders.length > 0 &&
        <table className='table is-striped is-fullwidth'>
          <thead>
            <tr>
              <th> Grader </th>
              <th> Solutions graded </th>
              <th> Average grading time </th>
              <th> Total grading time </th>
            </tr>
          </thead>
          <tbody>
            {
              props.graders.map((g, i) => {
                return (
                  <tr key={i}>
                    <td> {g.name} </td>
                    <td> {g.graded} </td>
                    <td> {formatTime(g.averageTime)} </td>
                    <td> {formatTime(g.totalTime)} </td>
                  </tr>
                )
              })
            }
          </tbody>
        </table>}

      {props.autograded > 0 &&
        <article className='message is-info'>
          <div className='message-body'>
            In this problem Zesje helped you grade
            {props.autograded === 1 ? ' 1 solution' : ` ${props.autograded} solutions`},
            saving you {formatTime(estimateGradingTime(props.graders) * props.autograded)} of grading time.
          </div>
        </article>}
    </>
  )
}

const estimateGradingTime = (graders) => {
  if (!graders.length) return 0

  const total = graders.reduce((s, g) => {
    s.graded += g.graded
    s.time += g.totalTime
    return s
  }, {
    graded: 0,
    time: 0
  })

  return total.time / total.graded
}

const ProblemsSummary = ({ problems, total, students, graders, changeProblem }) => {
  let totalUngraded = 0
  let totalInRevision = 0
  let totalTimeLeft = 0
  let totalFOs = 0
  const totalSolutions = problems.length * students

  const problemRows = problems.map((p, i) => {
    const avgTime = estimateGradingTime(p.graders)
    const solInRevision = p.inRevision
    const solToGrade = students - p.results.length
    let gradingTimeLeft = '-'

    totalUngraded += solToGrade
    totalInRevision += solInRevision
    totalTimeLeft += avgTime * solToGrade
    totalFOs += p.feedback.length

    if (students > p.results.length) {
      gradingTimeLeft = formatTime(solToGrade * avgTime)
    }

    return (
      <tr key={i}>
        <td style={{ textAlign: 'left' }}>
          <a onClick={e => changeProblem(p.id)}>{p.name}</a>
        </td>
        <td style={{ textAlign: 'right' }}>
          {p.feedback.length}
        </td>
        <td style={{ textAlign: 'right' }}>
          ({p.mean.value.toPrecision(2)} ± {p.mean.error.toPrecision(2)})/{p.max_score}
          = {(p.mean.value / p.max_score).toPrecision(2)}
        </td>
        <td style={{ textAlign: 'right' }}>
          {p.correlation !== null ? p.correlation.toPrecision(3) : '-'}
        </td>
        <td style={{ textAlign: 'right' }}>
          <div className={solInRevision > 0 ? 'tooltip has-tooltip-top' : 'has-tooltip-hidden'}
            data-tooltip={solInRevision > 0 ? `${solInRevision} needs revision` : ''}>
            {Math.round(100 * (p.results.length) / students)}%
          </div>
        </td>
        <td> {solToGrade === 0 ? '-' : `${gradingTimeLeft}`} </td>
      </tr>
    )
  })

  return <table className='table is-striped is-fullwidth'>
    <thead>
      <tr>
        <th> Problem </th>
        <th> Feedback count </th>
        <th> Avg. Score/Max Score </th>
        <th>
          <div className='has-tooltip-top has-tooltip-multiline'
            data-tooltip={'The correlation between a question and the rest of the questions.' +
            'Low or negative means that the question is likely random and does not correlate with learner\'s success.'}>
              Correlation (Rir)
          </div>
        </th>
        <th> Progress </th>
        <th> Estimated time left </th>
      </tr>
    </thead>
    <tbody>
      <tr key="0" style={{ borderBottom: '2pt solid lightgray' }}>
        <td style={{ textAlign: 'left' }}>
          <a onClick={e => changeProblem(0)}>Total</a>
        </td>
        <td style={{ textAlign: 'right' }}>
          <span className='has-tooltip-top' data-tooltip='Average number of feedback options per problem'>
            {parseInt(totalFOs / problems.length)}
          </span>
        </td>
        <td style={{ textAlign: 'right' }}>
          ({total.mean.value.toPrecision(2)} ± {total.mean.error.toPrecision(2)})/{total.max_score}
          = {(total.mean.value / total.max_score).toPrecision(2)}
        </td>
        <td style={{ textAlign: 'right' }}>
          {total.alpha !== null
            ? <div className="tooltip has-tooltip-top has-tooltip-multiline"
            data-tooltip={'Cronbach\'s α: The measure of whether the exam checks one or multiple skills.' +
              'A low value may indicate a need to review the learning goals.'}>
              α = {total.alpha.toPrecision(3)}</div>
            : '-'}
        </td>
        <td style={{ textAlign: 'right' }}>
          <div className={'tooltip ' + (totalInRevision > 0 ? 'has-tooltip-top' : 'has-tooltip-hidden')}
            data-tooltip={`${totalInRevision} needs revision`}>
            {Math.round(100 * (totalSolutions - totalUngraded) / totalSolutions)}%
          </div>
        </td>
        <td> {formatTime(totalTimeLeft)} </td>
      </tr>
      {
        problemRows
      }
    </tbody>
  </table>
}

class Overview extends React.Component {
  state = {
    stats: undefined,
    error: 'Loading statistics...',
    selectedProblemId: null,
    selectedStudentId: null
  }

  componentDidMount = () => {
    if (this.props.examID !== null) this.loadStats(this.props.examID)
  }

  componentDidUpdate = (prevProps, prevState) => {
    const examID = this.props.examID
    if (examID !== prevProps.examID) {
      this.setState({
        stats: undefined,
        error: '',
        selectedProblemId: null,
        selectedStudentId: null
      }, () => this.loadStats(examID))
    }
  }

  loadStats = (id) => {
    api.get(`stats/${id}`)
      .then(stats => this.setState({
        stats: stats,
        selectedProblemId: 0
      }))
      .catch(err => this.setState({
        stats: null,
        error: 'Error loading statistics: ' + err.message
      }))
  }

  changeProblem = (problemId) => {
    this.setState({ selectedProblemId: problemId })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  renderAtGlance = () => {
    const problems = this.state.stats.problems.slice()
    const total = this.state.stats.total
    const students = this.state.stats.students

    let totalUngraded = 0
    let totalInRevision = 0

    problems.forEach((p, i) => {
      totalUngraded += (students - p.results.length)
      totalInRevision += p.inRevision
    })

    problems.push({
      name: 'Total',
      id: 0,
      results: total.results,
      max_score: total.max_score,
      alpha: total.alpha
    })

    problems.reverse()

    const yVals = range(0, problems.length, 1).toArray()

    const annotations = []
    if (this.state.selectedStudentId) {
      problems.forEach((p, i) => {
        p.results.forEach((x, j) => {
          if (x.studentId === this.state.selectedStudentId) {
            const extratext = (
              p.id === 0 && x.ungraded > 0
                ? ' (provisional)'
                : !x.graded && p.id > 0 ? ' (to revise)' : ''
            )
            annotations.push({
              x: j,
              y: i,
              xref: 'x',
              yref: 'y',
              text: `${x.score}/${p.max_score}` + extratext,
              align: 'center',
              ay: 25,
              ax: 0,
              bgcolor: 'hsl(171, 100, 41)',
              arrowcolor: 'hsl(171, 100, 41)',
              font: {
                color: 'white'
              }
            })
          }
        })
      })

      annotations.push({
        x: 1,
        y: 1,
        xref: 'paper',
        yref: 'paper',
        yanchor: 'bottom',
        text: `Selected student: ${this.state.selectedStudentId}`,
        align: 'right',
        showarrow: false,
        bgcolor: 'hsl(171, 100, 41)',
        font: {
          color: 'white',
          size: 14
        }
      })
    }

    const data = [{
      type: 'heatmap',
      yaxis: 'y',
      y: yVals,
      z: problems.map(p => p.results.map(x => 100 * x.score / p.max_score)),
      ygap: 2,
      zmax: 100,
      zmin: 0,
      colorscale: 'Electric',
      colorbar: {
        title: {
          text: 'score (%)'
        },
        dtick: 10,
        y: 1,
        yanchor: 'top',
        len: 0.45
      },
      hoverongaps: false,
      hovertext: problems.map(p => p.results.map(x => {
        const baseText = `Student: ${x.studentId}<br>Score: ${x.score}/${p.max_score}`
        if (p.id === 0) { // the total bar
          return baseText +
            (x.ungraded > 0 ? `<br>${x.ungraded === 1 ? '1 problem' : `${x.ungraded} problems`} left to grade` : '')
        } else {
          return baseText + (x.graded ? '' : '<br><i>Needs revision</i>')
        }
      })),
      hoverinfo: 'text',
      hoverlabel: {
        bgcolor: 'hsl(217, 71, 53)' // primary
      },
      showlegend: false
    }]

    const histGraded = total.results.reduce((acc, v) => v.ungraded === 0 ? acc.concat(v.score) : acc, [])
    if (histGraded.length > 0) {
      data.push({
        x: histGraded,
        type: 'histogram',
        name: 'Graded',
        autobinx: false,
        xbins: {
          start: -0.5,
          end: total.max_score + 0.5,
          size: 1
        },
        hoverinfo: 'none',
        marker: {
          color: 'hsl(204, 86, 53)' // info
        },
        xaxis: 'x2',
        yaxis: 'y2'
      })
    }

    const histPartiallyGraded = total.results.reduce((acc, v) => v.ungraded > 0 ? acc.concat(v.score) : acc, [])
    if (histPartiallyGraded.length > 0) {
      data.push({
        x: histPartiallyGraded,
        type: 'histogram',
        name: 'Partially graded',
        autobinx: false,
        xbins: {
          start: -0.5,
          end: total.max_score + 0.5,
          size: 1
        },
        hoverinfo: 'none',
        marker: {
          color: 'hsla(204, 86, 53, 0.5)'
        },
        xaxis: 'x2',
        yaxis: 'y2'
      })
    }

    if (total.results.length > 1) {
      const norm = (sqrt(2 * pi) * total.mean.error)
      const xScores = range(0, total.max_score, 0.5).toArray()
      const yScores = xScores.map(x => {
        return total.results.length * exp(-pow((x - total.mean.value) / total.mean.error, 2) / 2) / norm
      })

      data.push({
        x: xScores,
        y: yScores,
        xaxis: 'x2',
        yaxis: 'y2',
        name: 'PDF',
        fill: 'tozeroy',
        type: 'scatter',
        mode: 'line',
        marker: {
          color: 'rgb(255, 0, 0)'
        },
        fillcolor: 'rgba(255, 0, 0, 0.1)',
        hoverinfo: 'none'
      })
    }

    annotations.push({
      x: 0.5,
      y: 0.35,
      xref: 'paper',
      yref: 'paper',
      yanchor: 'bottom',
      text: 'Histogram of scores<br>' +
        `(score = ${total.mean.value.toPrecision(2)} &#177; ${total.mean.error.toPrecision(2)})`,
      align: 'center',
      showarrow: false,
      font: {
        size: 25
      }
    })

    const layout = {
      xaxis: {
        title: 'number of students',
        range: [-0.5, students - 0.5],
        zeroline: false,
        domain: [0, 1],
        anchor: 'y',
        fixedrange: true
      },
      yaxis: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {
          size: 14
        },
        tickvals: yVals,
        ticktext: problems.map(p => {
          let color = 'black'
          if (p.id === 0) color = (totalUngraded + totalInRevision > 0 ? 'grey' : color)
          else color = (p.results.length - p.inRevision) < students ? 'grey' : color

          return `<span style="color:${color}">${p.name}</span>`
        }, []),
        zeroline: false,
        anchor: 'x',
        domain: [0.5, 1]
      },
      xaxis2: {
        domain: [0, 1],
        anchor: 'y2',
        zeroline: false,
        dtick: 5,
        title: 'score',
        fixedrange: true
      },
      yaxis2: {
        title: 'number of students',
        domain: [0, 0.35],
        anchor: 'x2',
        fixedrange: true
      },
      title: {
        text: 'At a glance',
        font: {
          size: 32
        }
      },
      legend: {
        y: 0.34,
        yanchor: 'top',
        x: 0.99,
        xanchor: 'right',
        borderwidth: 1
      },
      hovermode: 'closest',
      barmode: 'stack',
      plot_bgcolor: 'hsl(0,0,86)',
      height: 1000,
      annotations: annotations
    }

    const config = {
      displaylogo: false,
      scrollZoom: false,
      modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d',
        'hoverClosestCartesian', 'hoverCompareCartesian']
    }

    return (
      <>
        <Plot
          data={data}
          config={config}
          layout={layout}
          onClick={(data) => {
            const selProblem = problems[data.points[0].y]
            const selStudent = selProblem.results[data.points[0].x].studentId

            this.setState({ selectedStudentId: selStudent })
          }}
          onDoubleClick={() => this.setState({ selectedStudentId: null })}
          useResizeHandler
          style={{ width: '100%', position: 'relative', display: 'inline-block' }}
        />

      <ProblemsSummary
        problems={this.state.stats.problems}
        students={students}
        total={total}
        changeProblem={this.changeProblem} />

      {this.state.stats.copies / this.state.stats.students > 1.05 &&
        <article className='message is-warning'>
          <div className='message-body'>
            {this.state.stats.copies - this.state.stats.students} extra copies
            were needed to solve this exam by some students,
            consider adding more space the next time.
          </div>
        </article>}
      </>
    )
  }

  renderHistogramScores = (problem) => {
    const traces = []

    const histGraded = problem.results.reduce((acc, v) => v.graded ? acc.concat(v.score) : acc, [])
    if (histGraded.length > 0) {
      traces.push({
        x: histGraded,
        type: 'histogram',
        name: 'Graded',
        autobinx: false,
        xbins: {
          start: -0.5,
          end: problem.max_score + 0.5,
          size: 1
        },
        hoverinfo: 'none',
        marker: {
          color: 'hsl(204, 86, 53)'
        }
      })

      traces.push({ x: histGraded, type: 'histogram', yaxis: 'y2', visible: false, histnorm: 'percentage' })
    }

    const histRevise = problem.results.reduce((acc, v) => !v.graded ? acc.concat(v.score) : acc, [])
    if (histRevise.length > 0) {
      traces.push({
        x: histRevise,
        type: 'histogram',
        name: 'To revise',
        autobinx: false,
        xbins: {
          start: -0.5,
          end: problem.max_score + 0.5,
          size: 1
        },
        hoverinfo: 'none',
        marker: {
          color: 'hsla(204, 86, 53, 0.5)'
        }
      })
      traces.push({ x: histRevise, type: 'histogram', yaxis: 'y2', visible: false, histnorm: 'percentage' })
    }

    if (traces.length === 0) return null

    const layout = {
      xaxis: {
        title: 'score',
        zeroline: false,
        range: [-0.5, problem.max_score + 0.5],
        dtick: problem.max_score > 10 ? 5 : 1,
        fixedrange: true
      },
      yaxis: {
        title: 'number of students',
        fixedrange: true
      },
      yaxis2: {
        side: 'right',
        title: 'Percentage of students',
        overlaying: 'y',
        showgrid: false,
        anchor: 'x',
        range: [0, 100 / this.state.stats.students]
      },
      title: {
        text: 'Histogram of Scores<br>(score = ' +
          `${problem.mean.value.toPrecision(2)} ± ${problem.mean.error.toPrecision(2)})`
      },
      autosize: true,
      showlegend: true,
      barmode: 'stack',
      height: '150px'
    }

    const config = {
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d',
        'hoverClosestCartesian', 'hoverCompareCartesian']
    }

    return (
      <Plot
        data={traces}
        config={config}
        layout={layout}
        useResizeHandler
        style={{ width: '100%', position: 'relative', display: 'inline-block' }}
      />
    )
  }

  renderProblemSummary = (id) => {
    const problem = this.state.stats.problems.find(p => p.id === id)

    if (!problem) return null

    return (
      <>
        <div className='columns is-multiline'>
          <div className='column is-half-desktop is-full-mobile'>
            <h3 className='is-size-5'> Feedback details </h3>
            <table className='table is-striped is-fullwidth'>
              <thead>
                <tr>
                  <th> Feedback </th>
                  <th> Score </th>
                  <th> #&nbsp;Assigned</th>
                </tr>
              </thead>
              <tbody>
                {
                  problem.feedback.map((option, i) => {
                    return (
                      <tr key={i}>
                        <td>
                          {option.name}
                          <Tooltip text={option.description} />
                        </td>
                        <td> {option.score} </td>
                        <td> {option.used} </td>
                      </tr>
                    )
                  })
                }
              </tbody>
            </table>
          </div>
          <div className='column is-half-desktop is-full-mobile'>
            {this.renderHistogramScores(problem)}
          </div>
          <div className='column is-full'>
            <GraderDetails
              graders={problem.graders}
              autograded={problem.autograded}
            />
          </div>
        </div>
      </>
    )
  }

  render () {
    if (this.state.stats === undefined) {
      // stats are being loaded, we just want to show a loading screen
      return <Loading />
    }

    if (this.state.stats === null) {
      // no stats, show the error message
      return <Fail message={this.state.error} />
    }

    if (this.state.stats.problems.length === 0) {
      return <Fail message="No problems have been found to grade." />
    }

    return (
      <>
        <div className='has-text-centered'>
          <h1 className='is-size-1'> {this.state.stats.name} </h1>
          <span className='select is-medium'>
            <select
              value={this.state.selectedProblemId}
              onChange={(e) => {
                this.setState({
                  selectedProblemId: parseInt(e.target.value)
                })
              }}
            >
              <option key='key_0' value='0'>Overview</option>
              {this.state.stats.problems.map((problem, index) => {
                return <option key={'key_' + (index + 1)} value={problem.id}>{problem.name}</option>
              })}
            </select>
          </span>
          <section className='section'>
              {this.state.selectedProblemId === 0
                ? this.renderAtGlance()
                : this.renderProblemSummary(this.state.selectedProblemId)}
          </section>
        </div>
      </>
    )
  }
}

export default Overview

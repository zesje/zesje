import React from 'react'
import Plot from 'react-plotly.js'
import {range, exp, sqrt, pow, pi, zeros} from 'mathjs'

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

class Overview extends React.Component {
  state = {
    stats: null,
    loadingText: 'Loading statistics...',
    selectedProblemId: null,
    selectedStudentId: null
  }

  componentWillMount () {
    api.get(`stats/${this.props.examID}`)
      .then(stats => {
        this.setState({
          stats: stats,
          selectedProblemId: 0
        })
      }).catch(err => {
        console.log(err)
        err.json().then(res => {
          this.setState({
            stats: null,
            loadingText: 'Error loading statistics: ' + res.message
          })
        })
      })
  }

  renderAtGlance = () => {
    return (
      <React.Fragment>
        <div className='container'>

          {this.renderHeatmap()}

          {this.state.stats.copies / this.state.stats.students > 1.05 &&
            <article className='message is-warning'>
              <div className='message-body'>
                {this.state.stats.copies - this.state.stats.students} extra copies
                were needed to solve this exam by some students,
                consider adding more space the next time.
              </div>
            </article>
          }
        </div>
      </React.Fragment>
    )
  }

  renderHeatmap = () => {
    const problems = this.state.stats.problems.slice()
    const students = this.state.stats.students

    let totalUngraded = 0
    let totalInRevision = 0
    let totalTimeLeft = 0

    const labels = problems.map((p, i) => {
      if (!p.results.length) return p.name

      const avgTime = estimateGradingTime(p.graders)
      const solInRevision = p.inRevision
      const solToGrade = students - p.results.length

      totalUngraded += solToGrade
      totalInRevision += solInRevision
      totalTimeLeft += avgTime * solToGrade

      if (solToGrade || solInRevision) {
        const gradingTimeLeft = solToGrade * avgTime

        return (solToGrade ? `<br>${solToGrade} solutions to grade` : '') +
               (solInRevision > 0 ? `<br>${solInRevision} solutions to revise` : '') +
               `<br>Time left: ${formatTime(gradingTimeLeft)}`
      } else {
        return `Score: ${p.mean.value.toPrecision(1)} ± ${p.mean.error.toPrecision(1)}` +
               (p.correlation !== null ? `<br>Rir: ${p.correlation.toPrecision(3)}` : '')
      }
    })

    problems.push({
      name: 'Total',
      id: 0,
      results: this.state.stats.total.results,
      max_score: this.state.stats.total.max_score,
      alpha: this.state.stats.total.alpha
    })

    if (totalUngraded || totalInRevision) { // include in revision
      labels.push(`Time left: ${formatTime(totalTimeLeft)}<br>${totalUngraded} solutions to grade`)
    } else {
      labels.push(this.state.stats.total.alpha !== null ? `<br>Cronbach's α: ${this.state.stats.total.alpha.toPrecision(3)}` : '')
    }

    problems.reverse()
    labels.reverse()

    const yVals = range(0, problems.length, 1).toArray()

    const selectedData = []
    if (this.state.selectedStudentId) {
      problems.forEach((p, i) => {
        p.results.forEach((x, j) => {
          if (x.studentId === this.state.selectedStudentId) {
            const extratext = (
              p.id === 0 && x.ungraded > 0
                ? ' (provisional)'
                : !x.graded && p.id > 0 ? ' (to revise)' : ''
            )
            selectedData.push({
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

      selectedData.push({
        x: 1,
        y: 1.07,
        xref: 'paper',
        yref: 'paper',
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

    const total = this.state.stats.total
    let colorsFinished = 'hsl(204, 86, 53)'
    let colorsUnfinished = 'hsla(204, 86, 53, 0.5)'

    if (this.state.selectedStudentId) {
      const data = total.results.find(x => x.studentId === this.state.selectedStudentId)
      if (data) {
        if (data.graded) {
          colorsFinished = range(0, total.max_score + 1, 1).map(x => x === data.score ? 'hsl(171, 100, 41)' : 'hsl(204, 86, 53)').toArray()
        } else {
          colorsUnfinished = range(0, total.max_score + 1, 1).map(x => x === data.score ? 'hsla(171, 100, 41, 0.5)' : 'hsla(204, 86, 53, 0.5)').toArray()
        }
      }
    }

    const data = [{
      type: 'heatmap',
      y: yVals,
      showlegend: false
    }, {
      type: 'heatmap',
      yaxis: 'y2',
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
            (x.ungraded > 0 ? `<br>${x.ungraded} problems left to grade` : '')
        } else {
          return baseText + (x.graded ? '' : '<br><i>Needs revision</i>')
        }
      })),
      hoverinfo: 'text',
      hoverlabel: {
        bgcolor: 'hsl(217, 71, 53)'
      },
      showlegend: false
    }, {
      x: zeros(problems.length + 1).map(x => -2).toArray(),
      y: yVals,
      yaxis: 'y2',
      type: 'scatter',
      opacity: 0,
      mode: 'markers',
      size: 0,
      hoverinfo: 'text',
      hovertext: labels,
      hoverlabel: {
        bgcolor: 'hsl(0, 0, 96)',
        bordercolor: problems.map(p => {
          if (p.results.length === 0) {
            return 'hsl(348, 100, 61)'
          }
          return p.results.length === students ? 'hsl(141, 53, 53)' : 'hsl(48, 100%, 67%)'
        }),
        font: {
          color: '#000'
        },
        align: 'left'
      },
      showlegend: false
    }, {
      y: total.results.reduce((acc, v) => v.ungraded === 0 ? acc.concat(v.score) : acc, []),
      orientation: 'horizontal',
      type: 'histogram',
      name: 'Graded',
      autobinx: false,
      ybins: {
        start: -0.5,
        end: total.max_score + 0.5,
        size: 1
      },
      hoverinfo: 'none',
      marker: {
        color: colorsFinished
      },
      xaxis: 'x3',
      yaxis: 'y3'
    }, {
      y: total.results.reduce((acc, v) => v.ungraded > 0 ? acc.concat(v.score) : acc, []),
      orientation: 'horizontal',
      type: 'histogram',
      name: 'Partially graded',
      autobinx: false,
      ybins: {
        start: -0.5,
        end: total.max_score + 0.5,
        size: 1
      },
      hoverinfo: 'none',
      marker: {
        color: colorsUnfinished
      },
      xcalendar: 'gregorian',
      ycalendar: 'gregorian',
      xaxis: 'x3',
      yaxis: 'y3'
    }]

    if (total.results.length) {
      const norm = (sqrt(2 * pi) * total.mean.error)
      const xScores = range(0, total.max_score, 0.5).toArray()
      const yScores = xScores.map(x => {
        return total.results.length * exp(-pow((x - total.mean.value) / total.mean.error, 2) / 2) / norm
      })

      data.push({
        y: xScores,
        x: yScores,
        xaxis: 'x3',
        yaxis: 'y3',
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

    const layout = {
      xaxis: {
        title: 'number of students',
        range: [-0.5, students - 0.5],
        zeroline: false,
        domain: [0, 1],
        anchor: 'y'
      },
      yaxis: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {
          color: 'hsl(0,0,71)',
          size: 14
        },
        tickvals: problems.reduce((acc, p, i) => {
          if (p.id === 0 && totalUngraded > 0) return acc.concat(i)
          return p.results.length < students || students === 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          if (p.id === 0 && totalUngraded > 0) return acc.concat(p.name)
          return p.results.length < students || students === 0 ? acc.concat(p.name) : acc
        }, []),
        zeroline: false,
        anchor: 'x',
        domain: [0.55, 1]
      },
      yaxis2: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {
          color: 'hsl(0,0,7)',
          size: 14
        },
        tickvals: problems.reduce((acc, p, i) => {
          if (p.id === 0 && totalUngraded === 0) return acc.concat(i)
          return p.results.length === students && students > 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          if (p.id === 0 && totalUngraded === 0) return acc.concat(p.name)
          return p.results.length === students && students > 0 ? acc.concat(p.name) : acc
        }, []),
        zeroline: false,
        anchor: 'x',
        domain: [0.55, 1]
      },
      xaxis3: {
        domain: [0, 1],
        anchor: 'y3',
        zeroline: false,
        dtick: 5,
        side: 'top'
      },
      yaxis3: {
        title: 'score',
        domain: [0, 0.45],
        anchor: 'x3'
      },
      title: {
        text: 'At a glance',
        font: {
          family: 'Courier New',
          size: 32
        }
      },
      legend: {
        y: 0.44,
        yanchor: 'top',
        x: 0.99,
        xanchor: 'right',
        borderwidth: 1,
        title: {
          text: 'Histogram of scores',
          font: {size: 14}
        }
      },
      hovermode: 'closest',
      barmode: 'stack',
      plot_bgcolor: 'hsl(0,0,86)',
      height: 1000,
      annotations: selectedData
    }

    const config = {
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d',
        'zoomOut2d', 'zoomIn2d', 'zoom2d',
        'hoverClosestCartesian', 'hoverCompareCartesian']
    }

    return (<Plot
      data={data}
      config={config}
      layout={layout}
      onClick={(data) => {
        const selProblem = problems[data.points[0].y]
        const selStudent = selProblem.results[data.points[0].x].studentId

        this.setState({selectedStudentId: selStudent})
      }}
      onDoubleClick={() => this.setState({selectedStudentId: null})}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderHistogramScores = (problem) => {
    if (!problem.results.length) return null

    let colorsFinished = 'hsl(204, 86, 53)'
    let colorsUnfinished = 'hsla(204, 86, 53, 0.5)'

    if (this.state.selectedStudentId) {
      const data = problem.results.find(x => x.studentId === this.state.selectedStudentId)
      if (data) {
        if (data.graded) {
          colorsFinished = range(0, problem.max_score + 1, 1).map(x => x === data.score ? 'hsl(171, 100, 41)' : 'hsl(204, 86, 53)').toArray()
        } else {
          colorsUnfinished = range(0, problem.max_score + 1, 1).map(x => x === data.score ? 'hsla(171, 100, 41, 0.5)' : 'hsla(204, 86, 53, 0.5)').toArray()
        }
      }
    }

    const traces = [{
      x: problem.results.reduce((acc, v) => v.graded ? acc.concat(v.score) : acc, []),
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
        color: colorsFinished
      },
      xcalendar: 'gregorian',
      ycalendar: 'gregorian'
    }, {
      x: problem.results.reduce((acc, v) => !v.graded ? acc.concat(v.score) : acc, []),
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
        color: colorsUnfinished
      },
      xcalendar: 'gregorian',
      ycalendar: 'gregorian'
    }]

    const layout = {
      xaxis: {
        title: 'score',
        zeroline: false,
        dtick: problem.max_score > 10 ? 5 : 1
      },
      yaxis: {
        title: 'number of students'
      },
      title: {
        text: `Histogram of Scores<br>(score=${problem.mean.value.toPrecision(1)} ± ${problem.mean.error.toPrecision(1)})`
      },
      autosize: true,
      showlegend: true,
      barmode: 'stack',
      height: '150px'
    }

    const config = {
      displaylogo: false,
      modeBarButtonsToRemove: ['pan2d', 'select2d', 'lasso2d', 'resetScale2d',
        'zoomOut2d', 'zoomIn2d', 'zoom2d',
        'hoverClosestCartesian', 'hoverCompareCartesian']
    }

    return (<Plot
      data={traces}
      config={config}
      layout={layout}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderProblemSummary = (id) => {
    if (id === 0) {
      return this.renderAtGlance()
    }

    const problem = this.state.stats.problems.find(p => p.id === id)

    return (
      <React.Fragment>
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
          </div>
          <div className='column is-half-desktop is-full-mobile'>
            {this.renderHistogramScores(problem)}
          </div>
          <div className='column is-full'>
            <h3 className='is-size-5'> Grader details </h3>
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
                  problem.graders.map((g, i) => {
                    if (g.name === 'Zesje') return null

                    return <tr key={i}>
                      <td> {g.name} </td>
                      <td> {g.graded} </td>
                      <td> {formatTime(g.averageTime)} </td>
                      <td> {formatTime(g.totalTime)} </td>
                    </tr>
                  })
                }
              </tbody>
            </table>

            {problem.autograded > 0 &&
              <article className='message is-info'>
                <div className='message-body'>
                  In this problem Zesje helped you grade {problem.autograded === 1 ? '1 solution' : problem.autograded + ' solutions'},
                  saving you {formatTime(estimateGradingTime(problem.graders) * problem.autograded)} of grading time.
                </div>
              </article>
            }
          </div>
        </div>
      </React.Fragment>
    )
  }

  render () {
    return (
      <div>

        <Hero title='Overview' subtitle='Analyse the exam results' />

        { this.state.stats
          ? (
            <div className='container has-text-centered'>
              <h1 className='is-size-1'> {this.state.stats.name} </h1>
              <span className='select is-medium'>
                <select
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
                <div className='container'>
                  { this.renderProblemSummary(this.state.selectedProblemId) }
                </div>
              </section>
            </div>
          ) : (
            <div className='container'>
              <p className='container has-text-centered is-size-5'> {this.state.loadingText} </p>
            </div>
          )
        }

      </div >
    )
  }
}

export default Overview

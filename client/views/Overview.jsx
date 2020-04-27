import React from 'react'
import Plot from 'react-plotly.js'
import {mean, std, range, exp, sqrt, pow, pi, zeros} from 'mathjs'

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

const estimateGradingTimeLeft = (graders, totalSolutions) => {
  if (!graders.length) return 0

  const totalGraded = graders.reduce((s, g) => s + g.graded, 0)
  if (totalGraded === totalSolutions) return 0

  const totalTime = graders.reduce((s, g) => s + g.averageTime * g.graded, 0)

  return (totalSolutions - totalGraded) * totalTime / totalGraded
}

class Overview extends React.Component {
  state = {
    stats: null,
    selectedProblemId: null,
    selectedStudentId: null
  }

  componentWillMount () {
    console.log(this.props.examID)
    api.get(`stats/${this.props.examID}`)
      .then(stats => {
        console.log(stats)
        this.setState({
          stats: stats,
          selectedProblemId: 0
        })
      })
  }

  renderAtGlance = () => {
    const total = this.state.stats.total

    const graded = this.state.stats.problems.reduce((acc, p, i) => {
      if (!p.graders.length) return acc

      const n = p.graders.reduce((s, g, i) => s + g.graded, 0) + p.autograded

      acc.graded += n
      acc.averageTime += p.graders.reduce((s, g) => s + g.graded * g.averageTime, 0) / n
      return acc
    }, {
      graded: 0,
      averageTime: 0
    })

    const ungraded = this.state.stats.students * this.state.stats.problems.length - graded.graded
    graded.averageTime /= this.state.stats.problems.length

    return (
      <React.Fragment>
        <div className='container'>
          {ungraded > 0 &&
            <article className='message is-info'>
              <div className='message-body'>
                {ungraded === 1
                  ? 'There is just one solution left to grade.'
                  : `There are ${ungraded} solutions left to grade, this will approximately take you ${formatTime(ungraded * graded.averageTime)}.`
                }
              </div>
            </article>
          }

          {this.renderHeatmap()}

          {this.renderHistogramScores(total, true)}

          {this.state.stats.copies / this.state.stats.students > 1.1 &&
            <article className='message is-warning'>
              <div className='message-body'>
                {this.state.stats.copies - this.state.stats.students} extra copies
                where needed to solve this problem by some students,
                consider adding more space the next time.
              </div>
            </article>
          }
        </div>
      </React.Fragment>
    )
  }

  renderHeatmap = () => {
    if (this.state.stats.problems.length === 0) {
      return (
        <article className='message is-danger'>
          <div className='message-body'>
            The exam has no problems or there is no feedback assigned to them.
          </div>
        </article>
      )
    }

    const problems = this.state.stats.problems.slice().reverse()
    const students = this.state.stats.students

    const labels = problems.map((p, i) => {
      if (!p.results.length) return p.name

      const meanScore = mean(p.results.map(x => x.score / p.max_score))
      const stdScore = std(p.results.map(x => x.score / p.max_score))
      if (p.results.length < students) {
        const gradingTimeLeft = estimateGradingTimeLeft(p.graders, students)
        return `${p.name}<br>Time left: ${formatTime(gradingTimeLeft)}`
      } else {
        return `${p.name}<br>(` +
        `score = ${meanScore.toPrecision(3)} ± ${stdScore.toPrecision(2)}` +
        (p.correlation !== null ? `, Rir = ${p.correlation.toPrecision(3)})` : ')')
      }
    })

    const yVals = range(0, problems.length, 1).toArray()

    const selectedData = []
    if (this.state.selectedStudentId) {
      problems.forEach((p, i) => {
        p.results.forEach((x, j) => {
          if (x.studentId === this.state.selectedStudentId) {
            selectedData.push({
              x: j,
              y: i,
              xref: 'x',
              yref: 'y',
              text: `${x.score}/${p.max_score}`,
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
      console.log(selectedData)
    }

    const data = [{
      type: 'heatmap',
      y: yVals
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
        dtick: 10
      },
      hoverongaps: false,
      hovertext: problems.map(p => p.results.map(x => {
        return `Student: ${x.studentId}<br>Score: ${x.score}/${p.max_score}`
      })),
      hoverinfo: 'text',
      hoverlabel: {bgcolor: 'hsl(217, 71, 53)'}
    }]

    const layout = {
      xaxis: {
        title: 'number of students',
        range: [-0.5, students - 0.5],
        zeroline: false
      },
      yaxis: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {color: 'hsl(0,0,71)'},
        tickvals: problems.reduce((acc, p, i) => {
          return p.results.length < students || students === 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.results.length < students || students === 0 ? acc.concat(labels[i]) : acc
        }, []),
        zeroline: false
      },
      yaxis2: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {color: 'hsl(0,0,7)'},
        tickvals: problems.reduce((acc, p, i) => {
          return p.results.length === students && students > 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.results.length === students && students > 0 ? acc.concat(labels[i]) : acc
        }, []),
        zeroline: false
      },
      title: {
        text: 'At a glance',
        font: {
          family: 'Courier New',
          size: 32
        }
      },
      plot_bgcolor: 'hsl(0,0,86)',
      height: 550,
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
        const selProblem = this.state.stats.problems[this.state.stats.problems.length - data.points[0].y - 1]
        const selStudent = selProblem.results[data.points[0].x]['studentId']

        this.setState({selectedStudentId: selStudent})
      }}
      onDoubleClick={() => this.setState({selectedStudentId: null})}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderHistogramScores = (total, showPDF) => {
    if (!total.results.length) return null

    const vals = total.results.map(x => x.score)

    const colorsFinished = zeros(total.max_score + 1).toArray()
    const colorsUnfinished = zeros(total.max_score + 1).toArray()

    if (this.state.selectedStudentId) {
      const data = total.results.find(x => x.student === this.state.selectedStudentId)
      if (data) {
        if (data.graded) {
          colorsFinished[data.score] = 1
        } else {
          colorsUnfinished[data.score] = 1
        }
      }
    }

    const traces = [{
      x: total.results.reduce((acc, v) => {
        if (v.graded) acc.push(v.score)
        return acc
      }, []),
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
        color: colorsFinished,
        cmin: 0,
        cmax: 1,
        colorscale: [[0, 'hsl(204, 86, 53)'], [1, 'hsl(171, 100, 41)']]
      }
    }, {
      x: total.results.reduce((acc, v) => {
        if (!v.graded) acc.push(v.score)
        return acc
      }, []),
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
        color: colorsUnfinished,
        cmin: 0,
        cmax: 1,
        colorscale: [[0, 'hsla(204, 86, 53, 0.5)'], [1, 'hsla(171, 100, 41, 0.5)']],
        line: {
          color: 'green'
        }
      }
    }]

    const mu = mean(vals)
    const sigma = std(vals)

    if (showPDF) {
      const norm = (sqrt(2 * pi) * sigma)
      const xScores = range(0, total.max_score, 0.5).toArray()
      const yScores = xScores.map(x => {
        return vals.length * exp(-pow((x - mu) / sigma, 2) / 2) / norm
      })

      traces.push({
        x: xScores,
        y: yScores,
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
        title: 'score',
        zeroline: false,
        dtick: total.max_score > 10 ? 5 : 1
      },
      yaxis: {
        title: 'number of students'
      },
      title: {
        text: 'Histogram of Scores<br>' +
              `(score = ${mu.toPrecision(2)} ± ${sigma.toPrecision(2)}` +
              (total.alpha ? `, Cronbach's α: ${total.alpha.toPrecision(3)})` : ')')
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
            {this.renderHistogramScores(problem, false)}
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
                  saving you {formatTime(problem.averageGradingTime * problem.autograded)} of grading time.
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
                    console.log(e.target)
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
              <p className='container has-text-centered is-size-5'>Loading statistics...</p>
            </div>
          )
        }

      </div >
    )
  }
}

export default Overview

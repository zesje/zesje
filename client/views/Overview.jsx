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

const estimateGradingTime = (graders) => {
  if (!graders.length) return {graded: 0, time: 0}

  const total = graders.reduce((s, g) => {
    s.graded += g.graded
    s.time += g.totalTime
    return s
  }, {
    graded: 0,
    time: 0
  })

  total.time /= total.graded

  return total
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
    const total = this.state.stats.total

    return (
      <React.Fragment>
        <div className='container'>

          {this.renderHeatmap()}

          {this.renderHistogramScores(total, true)}

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

    const totalGraded = {
      graded: 0,
      averageTime: 0
    }

    const labels = problems.map((p, i) => {
      if (!p.results.length) return p.name

      const meanScore = mean(p.results.map(x => x.score / p.max_score))
      const stdScore = std(p.results.map(x => x.score / p.max_score))

      const total = estimateGradingTime(p.graders)
      totalGraded.graded += total.graded
      totalGraded.averageTime += total.averageTime
      const solInRevision = p.results.length - total.graded - p.autograded
      const solToGrade = students - p.results.length

      if (solToGrade || solInRevision) {
        const gradingTimeLeft = (students - p.autograded - total.graded) * total.time

        return `Time left: ${formatTime(gradingTimeLeft)}` +
               (solToGrade ? `<br>${solToGrade} solutions to grade` : '') +
               (solInRevision > 0 ? `<br>${solInRevision} solutions to revise` : '')
      } else {
        return `Score: ${meanScore.toPrecision(3)} ± ${stdScore.toPrecision(2)}` +
               (p.correlation !== null ? `<br>Rir: ${p.correlation.toPrecision(3)}` : '')
      }
    })

    const totalUngraded = this.state.stats.students * this.state.stats.problems.length - totalGraded.graded
    totalGraded.averageTime /= this.state.stats.problems.length

    problems.push({
      name: 'Total',
      results: this.state.stats.total.results,
      max_score: this.state.stats.total.max_score,
      alpha: this.state.stats.total.alpha
    })

    if (totalUngraded) {
      labels.push(`Time left: ${formatTime(totalGraded.averageTime * totalUngraded)}<br>${totalUngraded} solutions to grade`)
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
        return `Student: ${x.studentId}<br>` +
               `Score: ${x.score}/${p.max_score}` +
               (x.graded ? '' : p.name === 'Total' ? '<br><i>Some problems left</i>' : '<br><i>Needs revision</i>')
      })),
      hoverinfo: 'text',
      hoverlabel: {
        bgcolor: 'hsl(217, 71, 53)'
      }
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
        align: 'right'
      }
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
        tickfont: {
          color: 'hsl(0,0,71)',
          size: 14
        },
        tickvals: problems.reduce((acc, p, i) => {
          return p.results.length < students || students === 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.results.length < students || students === 0 ? acc.concat(p.name) : acc
        }, []),
        zeroline: false
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
          return p.results.length === students && students > 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.results.length === students && students > 0 ? acc.concat(p.name) : acc
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
      hovermode: 'closest',
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
        const selProblem = problems[data.points[0].y]
        const selStudent = selProblem.results[data.points[0].x].studentId

        this.setState({selectedStudentId: selStudent})
      }}
      onDoubleClick={() => this.setState({selectedStudentId: null})}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderHistogramScores = (total, showPDF) => {
    if (!total.results.length) return null

    const vals = total.results.map(x => x.score)

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
        color: colorsFinished
      },
      xcalendar: 'gregorian',
      ycalendar: 'gregorian'
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
        color: colorsUnfinished
      },
      xcalendar: 'gregorian',
      ycalendar: 'gregorian'
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
              `(score = ${mu.toPrecision(2)} ± ${sigma.toPrecision(2)})`
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
                  saving you {formatTime(estimateGradingTime(problem.graders).time * problem.autograded)} of grading time.
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

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

  const totalTime = graders.reduce((s, g) => s + g.avg_grading_time * g.graded, 0)

  return (totalSolutions - totalGraded) * totalTime / totalGraded
}

class Overview extends React.Component {
  state = {
    statsLoaded: false,
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
          statsLoaded: true,
          selectedProblemId: 0
        })
      })
  }

  renderAtGlance = () => {
    const total = this.state.stats.total

    const graded = this.state.stats.problems.reduce((acc, p, i) => {
      if (!p.graders.length) return acc

      acc.graded += p.graders.reduce((s, g, i) => s + g.graded, 0)
      acc.avg_grading_time += mean(p.graders.map(g => g.avg_grading_time))
      return acc
    }, {
      name: 'Graded',
      graded: 0,
      avg_grading_time: 0
    })

    graded.avg_grading_time /= this.state.stats.problems.length

    return (
      <React.Fragment>
        <div className='container'>
          {this.renderHeatmap()}

          {this.renderHistogramScores(total)}

          {this.renderBarGraded([graded], this.state.stats.students * this.state.stats.problems.length)}

          {total.extra_copies > 1 &&
            <article className='message is-warning'>
              <div className='message-body'>
                {total.extra_copies} extra copies where needed to solve this problem by some students,
                consider adding more space the next time.
              </div>
            </article>
          }
        </div>
      </React.Fragment>
    )
  }

  renderHeatmap = () => {
    const problems = this.state.stats.problems.slice().reverse()
    const students = this.state.stats.students

    const labels = problems.map((p, i) => {
      if (!p.scores.length) return p.name

      const meanScore = mean(p.scores.map(x => x.score / p.max_score))
      const stdScore = std(p.scores.map(x => x.score / p.max_score))
      if (p.scores.length < students) {
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
        p.scores.forEach((x, j) => {
          if (x.student === this.state.selectedStudentId) {
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
      z: problems.map(p => p.scores.map(x => x.score / p.max_score)),
      ygap: 2,
      xgap: 0.5,
      zmax: 1,
      zmin: 0,
      colorscale: 'Electric',
      colorbar: {
        title: {
          text: 'score'
        }
      },
      hoverongaps: false,
      hovertext: problems.map(p => p.scores.map(x => {
        return `Student: ${x.student}<br>Score: ${x.score}/${p.max_score}`
      })),
      hoverinfo: 'text',
      hoverlabel: {bgcolor: 'hsl(217, 71, 53)'}
    }]

    const layout = {
      xaxis: {
        title: 'number of students',
        range: [-0.5, students + 0.5],
        zeroline: false
      },
      yaxis: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {color: 'hsl(0,0,71)'},
        tickvals: problems.reduce((acc, p, i) => {
          return p.scores.length < students || students === 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.scores.length < students || students === 0 ? acc.concat(labels[i]) : acc
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
          return p.scores.length === students && students > 0 ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.scores.length === students && students > 0 ? acc.concat(labels[i]) : acc
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
      displaylogo: false
    }

    return (<Plot
      data={data}
      config={config}
      layout={layout}
      onClick={(data) => {
        const selProblem = this.state.stats.problems[this.state.stats.problems.length - data.points[0].y - 1]
        const selStudent = selProblem.scores[data.points[0].x]['student']

        this.setState({selectedStudentId: selStudent})
      }}
      onDoubleClick={() => this.setState({selectedStudentId: null})}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderHistogramScores = (total) => {
    if (!total.scores.length) return null

    const vals = total.scores.map(x => x.score)

    const colors = zeros(total.max_score).toArray()

    if (this.state.selectedStudentId) {
      const data = total.scores.find(x => x.student === this.state.selectedStudentId)
      if (data) {
        colors[data.score] = 1
      }
    }

    const traceHistogram = {
      x: vals,
      type: 'histogram',
      autobinx: false,
      xbins: {
        start: -0.5,
        end: total.max_score + 0.5,
        size: 1
      },
      hovertemplate: '%{y} students with a grade = %{x:.0f}<extra></extra>',
      hoverongaps: false,
      marker: {
        color: colors,
        cmin: 0,
        cmax: 1,
        colorscale: [[0, 'hsl(204, 86, 53)'], [1, 'hsl(171, 100, 41)']],
        line: {
          color: 'rgb(8,48,107)',
          width: 1.5
        }
      }
    }

    const xScores = range(0, total.max_score, 0.5).toArray()
    const mu = mean(vals)
    const sigma = std(vals)
    const norm = (sqrt(2 * pi) * sigma)
    const yScores = xScores.map(x => {
      return vals.length * exp(-pow((x - mu) / sigma, 2) / 2) / norm
    })

    const meanAnnotation = {
      x: mu,
      y: vals.length / norm,
      ax: 0,
      ay: 0,
      xref: 'x',
      yref: 'y',
      ayref: 'y',
      yanchor: 'top',
      arrowcolor: '#f00',
      text: `Mean: ${mu.toPrecision(2)} ± ${sigma.toPrecision(2)}`
    }

    const traceGaussian = {
      x: xScores,
      y: yScores,
      fill: 'tozeroy',
      type: 'scatter',
      mode: 'line',
      marker: {
        color: 'rgb(255, 0, 0)'
      },
      fillcolor: 'rgba(255, 0, 0, 0.2)',
      hoverinfo: 'none'
    }

    const layout = {
      xaxis: {
        title: 'score',
        zeroline: false,
        hoverformat: '.0f'
      },
      yaxis: {
        title: 'number of students'
      },
      title: {
        text: 'Histogram of Scores<br>' +
              (total.alpha ? `(Cronbach's α: ${total.alpha.toPrecision(3)})` : '')
      },
      autosize: true,
      showlegend: false,
      annotations: [meanAnnotation]
    }

    const config = {
      displaylogo: false
    }

    return (<Plot
      data={[traceGaussian, traceHistogram]}
      config={config}
      layout={layout}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderBarGraded = (graders, totalSolutions) => {
    if (!totalSolutions) return null

    graders.sort((g1, g2) => g2.graded - g1.graded)
    const gradedSubmissions = graders.reduce((acc, p, i) => acc + p.graded, 0)

    const traces = graders.map(g => {
      return {
        y: [''],
        x: [g.graded],
        name: g.name,
        type: 'bar',
        orientation: 'h',
        textposition: 'inside',
        texttemplate: g.name,
        hovertemplate: '<b>%{fullData.name}</b>: %{x} solutions<br>' +
                       `Average of ${formatTime(g.avg_grading_time)} per solution` +
                       '<extra></extra>',
        marker: {
          color: [g.graded],
          colorscale: 'Blues',
          reversescale: true,
          cmin: 0,
          cmax: gradedSubmissions,
          line: {
            width: 3
          }
        }
      }
    })

    if (gradedSubmissions < totalSolutions) {
      const approxTime = estimateGradingTimeLeft(graders, totalSolutions)
      traces.push({
        y: [''],
        x: [totalSolutions - gradedSubmissions],
        name: 'Ungraded',
        type: 'bar',
        orientation: 'h',
        textposition: 'inside',
        texttemplate: 'Ungraded',
        hovertemplate: '%{x} solutions<br>' +
                       `About ${formatTime(approxTime)} left` +
                       '<extra></extra>',
        marker: {
          color: 'hsl(0, 0, 86)',
          line: {width: 3}
        }
      })
    }

    const layout = {
      title: {
        text: 'Graded solutions',
        titlefont: {
          size: 16,
          family: 'Courier New'
        }
      },
      yaxis: {
        fixedrange: true
      },
      xaxis: {
        fixedrange: true,
        range: [0, totalSolutions]
      },
      barmode: 'stack',
      showlegend: false,
      height: 250,
      hovermode: 'closest'
    }

    const config = {
      displaylogo: false,
      editable: false
    }

    return (<Plot
      data={traces}
      config={config}
      layout={layout}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderFeedbackChart = (problem) => {
    const feedback = problem.feedback.sort((f1, f2) => f1.score - f2.score)

    const data = {
      y: feedback.map(f => f.used),
      x: feedback.map(f => f.name),
      text: feedback.map(f => f.description === null ? '' : f.description),
      type: 'bar',
      name: 'Used',
      marker: {
        color: feedback.map(f => f.score),
        cmin: 0,
        cmax: problem.max_score,
        colorscale: 'Electric',
        showscale: true,
        colorbar: {title: {text: 'score'}}
      },
      hovertemplate:
            'Used %{y} times<br><br>' +
            '%{text}' +
            '<extra></extra>'
    }

    const layout = {
      title: {
        text: 'Feedback Options',
        font: {
          family: 'Courier New',
          size: 16
        }
      },
      yaxis: {
        title: 'Used'
      }
    }

    const config = {
      displaylogo: false
    }

    return (<Plot
      data={[data]}
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

        {this.renderBarGraded(problem.graders, this.state.stats.students)}

        {problem.extra_solutions > 1 &&
          <article className='message is-warning'>
            <div className='message-body'>
              {problem.extra_solutions} extra solutions where needed to solve this problem by some students,
              consider adding more space the next time.
            </div>
          </article>
        }
      </React.Fragment>
    )
  }

  render () {
    return (
      <div>

        <Hero title='Overview' subtitle='Analyse the exam results' />

        { this.state.statsLoaded
          ? <div className='columns is-centered is-multiline'>
            <div className='column is-full has-text-centered'>
              <h1 className='is-size-1 has-text-centered'> {this.state.stats.name} </h1>
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
            </div>
            <div className={'column has-text-centered is-full-tablet ' + (this.state.selectedProblemId === 0
              ? 'is-three-fifths-desktop' : 'is-half-desktop')}>
              { this.renderProblemSummary(this.state.selectedProblemId) }
            </div>
          </div> : <p className='container has-text-centered is-size-5'>Loading statistics...</p> }
      </div >
    )
  }
}

export default Overview

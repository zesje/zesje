import React from 'react'
import Plot from 'react-plotly.js'
import {mean, std, range, exp, sqrt, pow, pi} from 'mathjs'

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

class Overview extends React.Component {
  state = {
    statsLoaded: false,
    stats: null,
    selectedProblemId: null
  }

  componentWillMount () {
    console.log(this.props.examID)
    api.get(`stats/${this.props.examID}`)
      .then(stats => {
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
        </div>
      </React.Fragment>
    )
  }

  renderHeatmap = () => {
    const problems = this.state.stats.problems.slice().reverse()
    const students = this.state.stats.students

    const labels = problems.map((p, i) => {
      const meanScore = mean(p.scores)
      const stdScore = std(p.scores)
      if (problems[i].scores.length < students) {
        return p.name
      } else {
        return `${p.name}<br>(Rir = ${p.correlation.toPrecision(3)}, ` +
        `score = ${meanScore.toPrecision(3)} ± ${stdScore.toPrecision(2)})`
      }
    })

    const data = [{
      type: 'heatmap',
      y: labels
    }, {
      type: 'heatmap',
      yaxis: 'y2',
      y: labels,
      z: problems.map(p => p.scores.map(x => x / p.max_score).sort()),
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
      hovertemplate: 'Score: %{z:.1f}<extra></extra>',
      hoverlabel: {bgcolor: 'hsl(217, 71, 53)'}
    }]

    const layout = {
      xaxis: {
        title: 'number of students'
      },
      yaxis: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {color: 'hsl(0,0,71)'},
        tickvals: problems.reduce((acc, p, i) => {
          return p.scores.length < students ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.scores.length < students ? acc.concat(labels[i]) : acc
        }, [])
      },
      yaxis2: {
        automargin: true,
        fixedrange: true,
        range: [-0.5, problems.length - 0.5],
        tickmode: 'array',
        tickfont: {color: 'hsl(0,0,7)'},
        tickvals: problems.reduce((acc, p, i) => {
          return p.scores.length === students ? acc.concat(i) : acc
        }, []),
        ticktext: problems.reduce((acc, p, i) => {
          return p.scores.length === students ? acc.concat(labels[i]) : acc
        }, [])
      },
      title: {
        text: 'At a glance',
        font: {
          family: 'Courier New',
          size: 32
        }
      },
      plot_bgcolor: 'hsl(0,0,86)',
      height: 550
    }

    const config = {
      displaylogo: false
    }

    return (<Plot
      data={data}
      config={config}
      layout={layout}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderHistogramScores = (total) => {
    const traceHistogram = {
      x: total.scores,
      type: 'histogram',
      autobinx: false,
      xbins: {
        start: -0.5,
        end: total.max_score + 0.5,
        size: 1
      },
      hovertemplate: '%{y} of students with a grade = %{x:.0f}<extra></extra>',
      hoverongaps: false,
      marker: {
        color: 'hsl(217, 71, 53)',
        line: {
          color: 'rgb(8,48,107)',
          width: 1.5
        }
      }
    }

    const xScores = range(0, total.max_score, 0.5).toArray()
    const mu = mean(total.scores)
    const sigma = std(total.scores)
    const yScores = xScores.map(x => {
      return 140 * exp(-pow((x - mu) / sigma, 2) / 2) / (sqrt(2 * pi) * sigma)
    })

    const traceGaussian = {
      x: xScores,
      y: yScores,
      fill: 'tozeroy',
      type: 'scatter',
      mode: 'line',
      marker: {
        color: 'rgb(255, 0, 0)'
      },
      fillcolor: 'rgba(255, 0, 0, 0.3)',
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
        text: `Histogram of Scores<br>(Cronbach's α: ${total.alpha.toPrecision(3)})`
      },
      autosize: true,
      showlegend: false
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
        hovertemplate: '%{x} solutions<br>' +
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
      const solutionsLeft = totalSolutions - gradedSubmissions
      const approxTime = solutionsLeft * mean(graders.map(g => g.avg_grading_time))
      traces.push({
        y: [''],
        x: [solutionsLeft],
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
        fixedrange: true
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
      </React.Fragment>
    )
  }

  render () {
    return (
      <div>

        <Hero title='Overview' subtitle='Analyse the exam results' />

        { this.state.statsLoaded
          ? <div className='columns is-centered'>
            <div className='column is-three-fifths-desktop is-full-mobile has-text-centered'>
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
              <div className='content'>
                { this.renderProblemSummary(this.state.selectedProblemId) }
              </div>
            </div>
          </div> : <p className='container has-text-centered is-size-5'>Loading statistics...</p> }
      </div >
    )
  }
}

export default Overview

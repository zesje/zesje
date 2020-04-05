import React from 'react'
import Plot from 'react-plotly.js'

import humanizeDuration from 'humanize-duration'
import Hero from '../components/Hero.jsx'
import * as api from '../api.jsx'

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
    selectedProblem: null
  }

  componentWillMount () {
    console.log(this.props.examID)
    api.get(`stats/${this.props.examID}`)
      .then(stats => {
        this.setState({
          stats: stats,
          statsLoaded: true,
          selectedProblem: stats.problems[0].name
        })
      })
  }

  renderAtGlance = () => {
    const total = this.state.stats.total

    let state = 'is-success'
    let message = 'This means that...'
    if (total.alpha < 0.5) {
      state = 'is-danger'
    } else if (total.alpha < 0.8) {
      state = 'is-warning'
    }

    return (
      <React.Fragment>
        <div className='container'>
          {this.renderHeatmap()}

          {this.renderHistogramScores(total.scores, total.max_score)}
          <article className={'message ' + state}>
            <div className='message-header'>
              <p>Cronbach's α: <strong>{total.alpha.toPrecision(3)}</strong></p>
            </div>
            <div className='message-body'>
              <p>
                {message}
                <br />
                Follow this <a href='https://en.wikipedia.org/wiki/Cronbach%27s_alpha' target='_blank'>link</a> for more reference.
              </p>
            </div>
          </article>
        </div>
      </React.Fragment>
    )
  }

  renderHeatmap = () => {
    const problems = this.state.stats.problems.slice().reverse()

    const data = {
      y: problems.map(p => `${p.name} (Rir = ${p.correlation.toPrecision(3)})`),
      z: problems.map(p => p.scores.map(x => x / p.max_score).sort()),
      ygap: 1,
      zmax: 1,
      zmin: 0,
      type: 'heatmap',
      colorscale: 'Electric',
      colorbar: {
        title: {
          text: 'score'
        }
      },
      hoverongaps: false,
      hovertemplate: 'Score: %{z:.1f}<extra>%{y}</extra>'
    }

    const layout = {
      xaxis: {
        title: 'number of students'
      },
      yaxis: {
        automargin: true,
        tickangle: -10,
        fixedrange: true
      },
      title: {
        text: 'At a glance',
        font: {
          family: 'Courier New',
          size: 32
        }
      },
      plot_bgcolor: '#DBDBDB'
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

  renderHistogramScores = (scores, maxScore) => {
    const data = {
      x: scores,
      type: 'histogram',
      histnorm: 'percent',
      cumulative: {enabled: true},
      autobinx: false,
      xbins: {
        start: -0.5,
        end: maxScore + 0.5,
        size: 1
      },
      hovertemplate: '%{y:.0f}% of students with a grade ≤ %{x:.0f}<extra></extra>',
      marker: {
        line: {
          color: 'rgb(8,48,107)',
          width: 1.5
        }
      }
    }

    const layout = {
      xaxis: {
        title: 'score',
        zeroline: false,
        hoverformat: '.0f'
      },
      yaxis: {
        title: 'percentage of students'
      },
      title: {
        text: 'Cumulative Probability Distribution'
      },
      autosize: true
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

  renderGraderGraded = (graders) => {
    const values = graders.map(g => g.graded)
    const labels = graders.map(g => g.name)
    const gradedSubmissions = values.reduce((a, b) => a + b, 0)

    if (gradedSubmissions < this.state.stats.students) {
      labels.push('Ungraded')
      values.push(this.state.stats.students - gradedSubmissions)
    }

    const data = {
      labels: labels,
      values: values,
      customdata: graders.map(g => `Average of ${formatTime(g.avg_grading_time)} per solution`),
      type: 'pie',
      sort: true,
      hovertemplate: '<b>%{label}</b><br>' +
                     '%{value} solutions<br>' +
                     '%{customdata}' +
                     '<extra></extra>'
    }

    const layout = {
      title: {
        text: 'Graders',
        font: {
          family: 'Courier New',
          size: 16
        }
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

  renderFeedbackChart = (feedback) => {
    const data = {
      y: feedback.map(f => f.used),
      x: feedback.map(f => f.name),
      text: feedback.map(f => f.description === null ? '' : f.description),
      type: 'bar',
      name: 'Used',
      hovertemplate:
            'Used: %{y}<br><br>' +
            '%{text}' +
            '<extra></extra>'
    }

    const score = {
      yaxis: 'y2',
      x: feedback.map(f => f.name),
      y: feedback.map(f => f.score),
      type: 'scatter',
      name: 'Score',
      hovertemplate:
            'Score: %{y}' +
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
        title: 'used',
        titlefont: {color: '#1f77b4'},
        tickfont: {color: '#1f77b4'},
        zeroline: true,
        showgrid: true
      },
      yaxis2: {
        title: 'score',
        side: 'right',
        overlaying: 'y',
        anchor: 'x',
        titlefont: {color: '#ff7f0e'},
        tickfont: {color: '#ff7f0e'},
        zeroline: false,
        showgrid: false
      }
    }

    const config = {
      displaylogo: false
    }

    return (<Plot
      data={[data, score]}
      config={config}
      layout={layout}
      useResizeHandler
      style={{width: '100%', position: 'relative', display: 'inline-block'}} />)
  }

  renderProblemSummary = (name) => {
    const results = this.state.stats.problems.find(p => p.name === name)

    return (
      <React.Fragment>
        {results.scores.length < this.state.stats.students &&
          <article className='message is-warning'>
            <div className='message-body'>
              <p>
                There are {this.state.stats.students - results.scores.length} solutions left to grade.
              </p>
            </div>
          </article>
        }

        <article className={'message ' + 'is-info'}>
          <div className='message-header'>
            <p>Rir coefficient: <strong>{results.correlation.toPrecision(3)}</strong></p>
          </div>
          <div className='message-body'>
            <p>
              The Rir coefficient (the correlation between a question and the rest of the questions). If this correlation becomes low or negative, the question is likely random and does not correlate with learner's success.
            </p>
          </div>
        </article>

        {this.renderHistogramScores(results.scores, results.max_score)}

        {this.renderFeedbackChart(results.feedback)}

        {this.renderGraderGraded(results.graders)}
      </React.Fragment>
    )
  }

  render () {
    return (
      <div>

        <Hero title='Overview' subtitle='Analyse the exam results' />

        { this.state.statsLoaded
          ? <div className='columns is-multiline is-centered'>
            <div className='column is-three-fifths-desktop is-full-mobile'>
              <h1 className='is-size-1 has-text-centered'>Exam "{this.state.stats.name}" </h1>
              {this.renderAtGlance()}
            </div>
            <div className='column is-half'>
              <h3 className='title is-size-2 has-text-centered'> Problem Details </h3>
              <span className='select is-fullwidth is-medium'>
                <select
                  onChange={(e) => {
                    this.setState({
                      selectedProblem: e.target.value
                    })
                  }}
                >
                  {this.state.stats.problems.map((problem, index) => {
                    return <option key={'key_' + index}>{problem.name}</option>
                  })}
                </select>
              </span>
              <section className='section'>
                { this.renderProblemSummary(this.state.selectedProblem) }
              </section>
            </div>
          </div> : <p className='container'>Loading statistics...</p> }
      </div >
    )
  }
}

export default Overview

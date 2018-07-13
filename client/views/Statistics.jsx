import React from 'react'

import Hero from '../components/Hero.jsx'

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
          <th> # assigned</th>
        </tr>
      </thead>
      <tbody>
        {
          props.problem.feedback.map((option, i) => (
            <tr key={i}>
              <th> {option.name} </th>
              <th> {option.score} </th>
              <th> {option.used} </th>
            </tr>
          ))
        }
      </tbody>
    </table>
  </React.Fragment>
)

class Statistics extends React.Component {

  render () {
    return (
      <div>

        <Hero title='Statistics' subtitle='Analyse how the exam was made' />

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
                <div className='column is-one-third-tablet' key={i}>
                  <div className='content'>
                    <ProblemSummary problem={problem} />
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

export default Statistics

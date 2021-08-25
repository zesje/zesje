import React from 'react'

class ProblemSelector extends React.Component {
  changeProblem = (event) => {
    this.props.navigateProblem(event.target.value)
    event.target.blur()
  }

  render () {
    return (
      <div className='field'>
        <label className='label'>Problem</label>
        <div
          className={'control has-icons-left' + (this.props.showTooltips ? ' tooltip has-tooltip-active' : '')}
          data-tooltip='previous problem: shift + ↑ next problem: shift + ↓'
        >
          <div className='select is-fullwidth'>
            <select
              value={this.props.current.id}
              onChange={this.changeProblem}
            >
              {this.props.problems.map((problem) =>
                <option key={problem.id} value={problem.id}>{problem.name}</option>
              )}
            </select>
          </div>
          <span className='icon is-left'>
            <i className='fa fa-question' />
          </span>
          <br />
        </div>
      </div>
    )
  }
}

export default ProblemSelector

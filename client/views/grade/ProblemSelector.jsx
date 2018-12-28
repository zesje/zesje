import React from 'react'

class ProblemSelector extends React.Component {
  render () {
    return (
      <div className='field'>
        <label className='label'>Problem</label>
        <div className={'control has-icons-left' + (this.props.showTooltips ? ' tooltip is-tooltip-active' : '')}
          data-tooltip='previous problem: shift + ↑ next problem: shift + ↓'>
          <div className='select is-fullwidth'>
            <select
              value={this.props.current}
              onChange={this.props.changeProblem}>
              {this.props.problems.map((problem, i) =>
                <option key={problem.id} value={i}>{problem.name}</option>
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

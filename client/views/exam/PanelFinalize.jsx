import React from 'react'

import * as api from '../../api.jsx'

class PanelFinalize extends React.Component {
  state = {
    examID: null,
    confirmationText: null,
    previewing: false
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    // In case nothing is set, use an empty function that no-ops
    if (prevState.examID !== nextProps.examID) {
      return {
        examID: nextProps.examID,
        confirmationText: nextProps.confirmationText,
        previewing: false
      }
    }

    return null
  }

  finalize = () => {
    api.put(`exams/${this.state.examID}`, { finalized: true })
      .then(() => {
        this.props.onFinalise()
        this.setState({ previewing: false })
      })
  }

  Finalize = (props) => {
    return (
      <button
        className='button is-link is-fullwidth'
        onClick={() => {
          this.setState({
            previewing: true
          })
        }}
      >
        Finalize
      </button>
    )
  }

  Delete = (props) => {
    return (
      <button
        className='button is-danger is-fullwidth'
        onClick={this.props.deleteExam}
      >
        Delete exam
      </button>
    )
  }

  render = () => {
    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Actions
        </p>
        {this.state.previewing ? (
          <div>
            <div className='panel-block'>
              <label className='label'>Finalize exam?</label>
            </div>
            <div className='panel-block'>
              {this.props.children}
            </div>
            <div className='panel-block field is-grouped'>
              <button
                className='button is-danger is-link is-fullwidth'
                onClick={this.finalize}
              >
                Yes
              </button>
              <button
                className='button is-link is-fullwidth'
                onClick={() => this.setState({ previewing: false })}
              >
                No
              </button>
            </div>
          </div>
        ) : (
          <div className='panel-block field is-grouped'>
            <this.Finalize />
            <this.Delete />
          </div>
        )}
      </nav>
    )
  }
}

export default PanelFinalize

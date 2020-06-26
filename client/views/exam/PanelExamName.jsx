import React from 'react'
import Notification from 'react-bulma-notification'

import Tooltip from '../../components/Tooltip.jsx'
import * as api from '../../api.jsx'

class PanelExamName extends React.Component {
  state = {
    examID: null,
    examName: '',
    editing: false
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.examID !== nextProps.examID) {
      return {
        examID: nextProps.examID,
        examName: nextProps.name,
        editing: false
      }
    }

    return null
  }

  inputColor = () => {
    if (this.state.examName) {
      if (this.state.examName !== this.props.name) {
        return 'is-success'
      } else {
        return 'is-link'
      }
    } else {
      return 'is-danger'
    }
  }

  saveName = (name) => {
    api.patch(`exams/${this.props.examID}`, {name: name})
      .then(() => {
        this.setState({
          examName: name,
          editing: false
        })

        this.onChange()
      })
      .catch(err => {
        this.setState({
          examName: this.props.name,
          editing: false
        })
        console.log(err)
        err.json().then(e => {
          Notification.error('Could not save exam name: ' + e.message)
        })
      })
  }

  onChange = () => {
    // In order to change the name everywhere in the UI we need to update the exam
    // in the parent view and reload the exam list in the navbar
    this.props.updateExam()
    this.props.updateExamList()
  }

  render = () => (
    <nav className='panel'>
      <p className='panel-heading'>
        Exam details
      </p>
      {this.state.editing ? (
        <React.Fragment>
          <div className='panel-block'>
            <input className={'input ' + this.inputColor()}
              type='text'
              placeholder='Exam name'
              value={this.state.examName}
              onChange={(e) => {
                this.setState({
                  examName: e.target.value
                })
              }} />
          </div>
          <div className='panel-block buttons is-right'>
            <button
              className='button is-danger'
              style={{marginBottom: '0'}}
              onClick={() => {
                this.setState({
                  examName: this.props.name,
                  editing: false
                })
              }}
            >
              Cancel
            </button>
            <button
              className='button is-link'
              style={{marginBottom: '0'}}
              disabled={this.state.examName === this.props.name || this.state.examName === ''}
              onClick={() => { this.saveName(this.state.examName) }}
            >
              Save
            </button>
          </div>
        </React.Fragment>
      ) : (
        <div className='panel-block'>
          <p className='is-size-3'>
            {this.state.examName}
          </p>
          <Tooltip
            icon='pencil'
            location='top'
            text='Click to edit the exam name.'
            clickAction={() => this.setState({editing: true})}
          />
        </div>
      )}
    </nav>
  )
}

export default PanelExamName

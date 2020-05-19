import React from 'react'
import Notification from 'react-bulma-notification'

import Tooltip from '../../components/Tooltip.jsx'
import * as api from '../../api.jsx'

class PanelExamName extends React.Component {
  state = {
    examName: '',
    editing: false
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (this.props.name !== prevProps.name) {
      this.setState({
        examName: this.props.name,
        editing: false
      })
    }
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

  render = () => {
    return this.state.editing ? (
      <nav className='panel'>
        <p className='panel-heading'>
          Exam details
        </p>
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
        <div className='panel-block field is-grouped'>
          <button
            className='button is-danger is-link is-fullwidth'
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
            className='button is-link is-fullwidth'
            disabled={this.state.examName === this.props.name || this.state.examName === ''}
            onClick={() => {
              api.patch(`exams/${this.props.examID}`, {name: this.state.examName})
                .then(() => {
                  this.setState({editing: false})

                  this.props.onChange(this.state.examName)
                })
                .catch(err => {
                  console.log(err)
                  err.json().then(e => {
                    Notification.error('Could not save exam name: ' + e.message)
                  })
                })
            }}
          >
            Save
          </button>
        </div>
      </nav>
    ) : (
      <nav className='panel'>
        <p className='panel-heading'>
          Exam details
        </p>
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
      </nav>
    )
  }
}

export default PanelExamName

import React from 'react'
import { toast } from 'bulma-toast'
import Switch from '../../components/Switch.jsx'

import * as api from '../../api.jsx'

class PanelGradeAnonymous extends React.Component {
  state = {
    examID: null,
    gradeAnonymous: false,
    isLoading: false,
    text: null
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    // In case nothing is set, use an empty function that no-ops
    const onChange = nextProps.onChange || ((_, anonymous) => {})
    if (prevState.examID !== nextProps.examID) {
      return {
        examID: nextProps.examID,
        gradeAnonymous: nextProps.gradeAnonymous,
        text: nextProps.text,
        isLoading: false,
        onChange: onChange
      }
    }

    return { onChange: onChange }
  }

  toogleGradeAnonymous = () => {
    this.setState({ isLoading: true }, () =>
      api.put(`exams/${this.state.examID}`, { grade_anonymous: !this.state.gradeAnonymous })
        .then(() => {
          this.setState({
            gradeAnonymous: !this.state.gradeAnonymous,
            isLoading: false
          }, () => this.props.onChange && this.props.onChange(this.state.gradeAnonymous))
        })
        .catch(err => {
          if (err.status === 409) toast({ message: err.message, type: 'is-warning' })
          else toast({ message: 'Could not change Grade Anonymous setting: ' + err.message, type: 'is-danger' })
          this.setState({ isLoading: false })
        })
    )
  }

  render = () => (
    <nav className='panel'>
      <p className='panel-heading'>
        Anonymous grading
      </p>
      <div className='panel-block'>
        <div className='field flex-input'>
          <label>Hide student info when grading</label>
          <Switch
            color='link'
            disabled={this.state.isLoading}
            value={this.state.gradeAnonymous}
            onChange={(e) => this.toogleGradeAnonymous()}
          />
        </div>
      </div>
      {this.state.text && <div className='panel-block'>
        {this.state.text}
      </div>}
    </nav>
  )
}

export default PanelGradeAnonymous

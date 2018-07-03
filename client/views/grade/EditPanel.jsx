import React from 'react'

import * as api from '../../api.jsx'

const BackButton = (props) => (
  <button className='button is-light is-fullwidth' onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-chevron-left' />
    </span>
    <span>back</span>
  </button>
)

const SaveButton = (props) => (
  <button className='button is-link is-fullwidth' disabled={props.disabled} onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-floppy-o' />
    </span>
    <span>{props.exists ? 'save' : 'add'}</span>
  </button>
)

class EditPanel extends React.Component {
  state = {
    id: null,
    name: '',
    description: '',
    score: ''
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (nextProps.feedback && prevState.id !== nextProps.feedback.id) {
      const fb = nextProps.feedback
      return {
        id: fb.id,
        name: fb.name,
        description: fb.description,
        score: fb.score
      }
    }
    return null
  }

  changeText = (event) => {
    this.setState({
      [event.target.name]: event.target.value
    })
  }
  changeScore = (event) => {
    const patt = new RegExp(/^(-|(-?[1-9]\d*)|0)?$/)

    if (patt.test(event.target.value)) {
      this.setState({
        score: event.target.value
      })
    }
  }

  key = (event) => {
    if (event.keyCode === 13 && this.state.name.length) {
      this.saveFeedback()
    }
  }

  saveFeedback = () => {
    const uri = 'feedback/' + this.props.problemID
    const fb = {
      name: this.state.name,
      description: this.state.description,
      score: this.state.score
    }

    if (this.state.id) {
      fb.id = this.state.id
      api.put(uri, fb)
        .then(() => this.props.goBack)
    } else {
      api.post(uri, fb)
        .then(() => {
          this.setState({
            id: null,
            name: '',
            description: '',
            score: ''
          })
        })
    }
  }

  render () {
    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Manage feedback
        </p>

        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Name</label>
            <div className='control has-icons-left'>
              <input className='input' placeholder='Name' name='name'
                value={this.state.name} onChange={this.changeText} onKeyDown={this.key} />
              <span className='icon is-small is-left'>
                <i className='fa fa-quote-left' />
              </span>
            </div>
          </div>
        </div>

        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Description</label>
            <div className='control has-icons-left'>
              <textarea className='input' rows='2' placeholder='Description' name='description'
                value={this.state.description} onChange={this.changeText} onKeyDown={this.key} />
              <span className='icon is-small is-left'>
                <i className='fa fa-comment-o' />
              </span>
            </div>
          </div>
        </div>

        <div className='panel-block'>
          <div className='field'>
            <label className='label'>Score</label>
            <div className='control has-icons-left has-icons-right'>
              <input className='input' placeholder='Score'
                value={this.state.score} onChange={this.changeScore} onKeyDown={this.key} />
              <span className='icon is-small is-left'>
                <i className='fa fa-star' />
              </span>
            </div>
          </div>
        </div>

        <div className='panel-block'>
          <BackButton onClick={this.props.goBack} />
          <SaveButton onClick={this.saveFeedback} exists={this.props.feedback}
            disabled={!this.state.name || !this.state.score || isNaN(parseInt(this.state.score))} />
        </div>
      </nav>
    )
  }
}

export default EditPanel

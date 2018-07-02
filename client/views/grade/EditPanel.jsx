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
    <span>{props.exists ? 'edit' : 'add'}</span>
  </button>
)

class EditPanel extends React.Component {
  state = {
    name: '',
    description: '',
    score: ''
  }

  componentWillMount = () => {
    if (this.props.feedback) {
      this.setState(this.props.feedback)
    }
  }

  changeName = (event) => {
    this.setState({
      name: event.target.value
    })
  }
  changeDesc = (event) => {
    this.setState({
      description: event.target.value
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
      console.log(this.state)
      this.saveFeedback()
    }
  }

  saveFeedback = () => {
    let save = this.props.feedback ? api.put : api.post

    save('feedback/' + this.props.problem.id, this.state)
      .then(feedback => {
        console.log(feedback)
        this.props.goBack()
      })
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
              <input className='input' placeholder='Name'
                value={this.state.name} onChange={this.changeName} onKeyDown={this.key} />
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
              <textarea className='input' rows='2' placeholder='Description'
                value={this.state.description} onChange={this.changeDesc} onKeyDown={this.key} />
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
            disabled={!this.state.name || (this.state.score && isNaN(parseInt(this.state.score)))} />
        </div>
      </nav>
    )
  }
}

export default EditPanel

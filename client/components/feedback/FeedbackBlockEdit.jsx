import React from 'react'

import ConfirmationModal from '../ConfirmationModal.jsx'
import ColorInput from '../ColorInput.jsx'
import * as api from '../../api.jsx'
import Notification from 'react-bulma-notification'

const CancelButton = (props) => (
  <button className='button is-light' onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-times' />
    </span>
    <span>Cancel</span>
  </button>
)

const SaveButton = (props) => (
  <button className='button is-link' disabled={props.disabled} onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-floppy-o' />
    </span>
    <span>{props.exists ? 'Save' : 'Add'}</span>
  </button>
)

const DeleteButton = (props) => (
  <button className='button is-danger' style={{marginLeft: 'auto'}} disabled={!props.exists} onClick={props.onClick}>
    <span className='icon is-small'>
      <i className='fa fa-trash' />
    </span>
  </button>
)

class EditPanel extends React.Component {
  state = {
    id: null,
    name: '',
    description: '',
    score: '',
    deleting: false
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    // In case nothing is set, use an empty function that no-ops
    const updateCallback = nextProps.updateFeedback || (_ => {})
    if (nextProps.feedback && prevState.id !== nextProps.feedback.id) {
      const fb = nextProps.feedback
      return {
        id: fb.id,
        name: fb.name,
        description: fb.description === null ? '' : fb.description,
        score: fb.score,
        parent: fb.parent,
        updateCallback: updateCallback
      }
    }
    return {updateCallback: updateCallback}
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
    if (!event.shiftKey && event.keyCode === 13 && this.state.name.length) {
      this.saveFeedback()
    }
  }

  saveFeedback = () => {
    const uri = 'feedback/' + this.props.problemID
    const fb = {
      name: this.state.name,
      description: this.state.description,
      score: this.state.score,
      parent: this.props.parent != null ? this.props.parent.id : null
    }

    if (this.state.id) {
      fb.id = this.state.id
      api.put(uri, fb)
        .then(() => {
          this.state.updateCallback()
          this.props.goBack()
        })
    } else {
      api.post(uri, fb)
        .then((response) => {
          // Response is the feedback option
          this.state.updateCallback()
          this.setState({
            id: null,
            name: '',
            description: '',
            score: ''
          })
        })
    }
  }

  deleteFeedback = () => {
    if (this.state.id) {
      api.del('feedback/' + this.props.problemID + '/' + this.state.id)
        .then(() => {
          this.state.updateCallback()
          this.props.goBack()
        })
        .catch(err => {
          err.json().then(res => {
            Notification.error('Could not delete feedback' +
              (res.message ? ': ' + res.message : ''))
            // update to try and get a consistent state
            this.state.updateCallback()
            this.props.goBack()
          })
        })
    }
  }

  render () {
    let children = null
    if (this.props.feedback !== null) {
      children = this.props.children.map((child, index) => this.props.feedbackPanel.getFeedbackElement(child, child.index, this.props.feedbackPanel))
    }
    return (
      <React.Fragment>
        <div className={this.props.parent != null ? 'panel-block attach-bottom' : ''}>
          {this.props.parent != null
            ? this.props.parent.parent === null ? <div>Add on top-level</div> : <div>Adds to parent: {this.props.parent.name}</div>
            : null}
        </div>
        <div className={this.props.parent != null ? 'panel-block attach-bottom' : ''}>
          <div className='field-body'>
            <div className='field no-grow'>
              <p className='label'>Score</p>
              <div className='control is-score-control'>
                <ColorInput
                  placeholder='7'
                  value={this.state.score}
                  onChange={this.changeScore}
                  onKeyDown={this.key} />
              </div>
            </div>
            <div className='field grow'>
              <p className='label'>Name</p>
              <div className='control'>
                <ColorInput
                  placeholder='e.g. Correct solution'
                  name='name'
                  value={this.state.name}
                  onChange={this.changeText}
                  onKeyDown={this.key} />
              </div>
            </div>
          </div>
        </div>
        <div className={this.props.parent != null ? 'panel-block attach-bottom' : ''}>
          <div className='field is-fullwidth'>
            <label className='label'>Description</label>
            <div className='control has-icons-left'>
              <textarea className='input'
                style={{height: '4rem'}}
                placeholder='Description'
                name='description'
                value={this.state.description}
                onChange={this.changeText}
                onKeyDown={this.key} />
              <span className='icon is-small is-left'>
                <i className='fa fa-comment-o' />
              </span>
            </div>
          </div>
        </div>
        <div className={this.props.parent != null ? 'panel-block' : ''}>
          <div className={'flex-space-between is-fullwidth'}>
            <div className={'buttons is-marginless'}>
              <SaveButton onClick={this.saveFeedback} exists={this.props.feedback}
                disabled={!this.state.name || (!this.state.score && this.state.score !== 0) || isNaN(parseInt(this.state.score))} />
              <CancelButton onClick={this.props.goBack} />
            </div>
            <DeleteButton onClick={() => { this.setState({deleting: true}) }} exists={this.props.feedback} />
          </div>
          <ConfirmationModal
            headerText={`Do you want to irreversibly delete feedback option "${this.state.name}"?`}
            contentText={this.props.feedback && (this.props.feedback.used || this.props.feedback.children != null)
              ? (this.props.feedback.children.length > 0 ? 'This feedback has ' + (this.props.feedback.children.length > 1 ? `${this.props.feedback.children.length} children` : ' 1 child') +
              ', that would also be deleted in the process. ' : '') +
              (this.props.feedback.used ? 'This feedback option was assigned to ' +
              (this.props.feedback.used > 1 ? `${this.props.feedback.used} solutions` : ' 1 solution') +
              ' and it will be removed. This will affect the final grade assigned to each submission.'
                : '')
              : 'This feedback option is not used and has no children, you can safely delete it.'
            }
            color='is-danger' confirmText='Delete feedback'
            active={this.state.deleting}
            onConfirm={this.deleteFeedback}
            onCancel={() => { this.setState({deleting: false}) }}
          />
        </div>
        {this.props.feedback !== null && children.length > 0 ? <ul className='menu-list'> {children} </ul> : null}
      </React.Fragment>
    )
  }
}

export default EditPanel

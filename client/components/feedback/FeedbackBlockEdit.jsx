import React from 'react'

import ConfirmationModal from '../modals/ConfirmationModal.jsx'
import ColorInput from '../ColorInput.jsx'
import Switch from '../Switch.jsx'
import { HasModalContext } from '../../views/Grade.jsx'
import * as api from '../../api.jsx'
import { toast } from 'bulma-toast'

import { FeedbackList } from './FeedbackUtils.jsx'

const CancelButton = (props) => (
  <button className='button is-light tooltip' onClick={props.onClick} data-tooltip='Cancel'>
    <span className='icon is-small'>
      <i className='fa fa-times' />
    </span>
  </button>
)

const SaveButton = (props) => (
  <button className='button is-link tooltip' disabled={props.disabled} onClick={props.onClick}
    data-tooltip={props.exists ? 'Save' : 'Add'}>
    <span className='icon is-small'>
      <i className='fa fa-save' />
    </span>
  </button>
)

const DeleteButton = (props) => (
  <button className='button is-danger tooltip'
    style={{ marginLeft: 'auto' }} disabled={!props.disabled} onClick={props.onClick} data-tooltip='Delete'>
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
    exclusive: false,
    deleting: false
  }

  static contextType = HasModalContext

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
        exclusive: nextProps.indexedFeedback[fb.parent].exclusive,
        updateCallback: updateCallback
      }
    }
    return { updateCallback: updateCallback }
  }

  changeText = (event) => {
    this.setState({
      [event.target.name]: event.target.value
    })
  }

  changeScore = (event) => {
    const patt = /^(-|(-?[1-9]\d*)|0)?$/

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
      score: this.state.score
    }

    if (this.state.id) {
      Promise.all([
        api.patch(uri + `/${this.state.id}`, fb),
        (this.state.exclusive !== this.props.parentExclusive
          ? api.patch(uri + `/${this.props.parentId}`, { exclusive: this.state.exclusive })
          : Promise.resolve({ set_aside_solutions: 0 }))
      ])
        .then(([r1, r2]) => {
          this.state.updateCallback()
          this.props.goBack()

          if (r2.set_aside_solutions > 0) {
            toast({
              message: `${r2.set_aside_solutions} solution${r2.set_aside_solutions > 1 ? 's have' : ' has'} ` +
                'been marked as ungraded due to incompatible feedback options.',
              type: 'is-warning',
              duration: 5000
            })
          }
        })
        .catch(err => {
          console.log(err)
        })
    } else {
      fb.parentId = this.props.parentId
      api.post(uri, fb)
        .then((response) => {
          // Response is the feedback option
          this.state.updateCallback()
          this.setState({
            id: null,
            name: '',
            description: '',
            score: '',
            parent: null,
            exclusive: false
          })
        })
        .catch(err => {
          console.log(err)
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
          toast({
            message: 'Could not delete feedback' + (err.message ? ': ' + err.message : ''),
            type: 'is-danger'
          })
          // update to try and get a consistent state
          this.state.updateCallback()
          this.props.goBack()
        })
    }
  }

  render () {
    return (
      <HasModalContext.Consumer>{updateHasModal => (<React.Fragment>
        {this.props.parent && <div className='panel-block attach-bottom'>
          {this.props.parent.parent === null
            ? <div>Add on top-level</div>
            : <div><b>Parent feedback:</b> {this.props.parent.name}</div>}
        </div>}
        <div className={this.props.parent !== null ? 'panel-block attach-bottom' : ''}>
          <div className='field-body'>
            <div className='field no-grow'>
              <p className='label'>Score</p>
              <div className='control is-score-control'>
                <ColorInput
                  placeholder='7'
                  value={this.state.score}
                  onChange={this.changeScore}
                  onKeyDown={this.key}
                />
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
                  onKeyDown={this.key}
                />
              </div>
            </div>
          </div>
        </div>
        <div className={this.props.parent !== null ? 'panel-block attach-bottom' : ''}>
          <div className='field is-fullwidth'>
            <label className='label'>Description</label>
            <div className='control has-icons-left'>
              <textarea
                className='input'
                style={{ height: '4rem' }}
                placeholder='Description'
                name='description'
                value={this.state.description}
                onChange={this.changeText}
                onKeyDown={this.key}
              />
              <span className='icon is-small is-left'>
                <i className='fa fa-comment' />
              </span>
            </div>
          </div>
        </div>
        {this.state.id &&
          <div className={this.props.parent !== null ? 'panel-block attach-bottom' : ''}>
            <div className='field is-grouped is-fullwidth'>
              <p className='control is-expanded'>
                <label className='label'>Exclusive</label>
              </p>
              <Switch
                color='link'
                value={this.state.exclusive}
                onChange={() => this.setState({ exclusive: !this.state.exclusive })}
              />
            </div>
          </div>
        }
        <div className={this.props.parent !== null ? 'panel-block' : ''}>
          <div className='flex-space-between is-fullwidth'>
            <div className='buttons is-marginless'>
              <SaveButton onClick={this.saveFeedback} exists={this.props.feedback}
                disabled={!this.state.name ||
                  (!this.state.score && this.state.score !== 0) ||
                  isNaN(parseInt(this.state.score))} />
              <CancelButton onClick={this.props.goBack} />
            </div>
            <DeleteButton
              onClick={() => { this.setState({ deleting: true }, () => updateHasModal(true)) }}
              disabled={this.props.feedback} />
          </div>
          <ConfirmationModal
            headerText={`Do you want to irreversibly delete feedback option "${this.state.name}"?`}
            contentText={this.props.feedback && (this.props.feedback.used || this.props.feedback.children != null)
              ? (this.props.feedback.children.length > 0
                  ? 'This feedback has ' + (this.props.feedback.children.length > 1
                    ? `${this.props.feedback.children.length} children`
                    : ' 1 child') +
              ', that would also be deleted in the process. '
                  : '') +
                (this.props.feedback.used
                  ? 'This feedback option was assigned to ' +
                  (this.props.feedback.used > 1 ? `${this.props.feedback.used} solutions` : ' 1 solution') +
                  ' and it will be removed. This will affect the final grade assigned to each submission.'
                  : '')
              : 'This feedback option is not used and has no children, you can safely delete it.'
            }
            color='is-danger'
            confirmText='Delete feedback'
            active={this.state.deleting}
            onConfirm={this.deleteFeedback}
            onCancel={() => { this.setState({ deleting: false }, () => updateHasModal(false)) }}
          />
        </div>
        {this.props.feedback && <FeedbackList {...this.props.parentProps} feedback={this.props.feedback} />}
      </React.Fragment>)}</HasModalContext.Consumer>
    )
  }
}

export default EditPanel

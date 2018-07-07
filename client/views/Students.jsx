import React from 'react'
import Mousetrap from 'mousetrap'

import * as api from '../api.jsx'

import Hero from '../components/Hero.jsx'
import ProgressBar from '../components/ProgressBar.jsx'

import SearchPanel from './students/SearchPanel.jsx'
import EditPanel from './students/EditPanel.jsx'

class CheckStudents extends React.Component {
  state = {
    editActive: false,
    editStud: null,
    input: '',
    index: 0,
    examID: null
  };

  componentWillUnmount = () => {
    Mousetrap.unbind(['left', 'h'])
    Mousetrap.unbind(['right', 'l'])
    Mousetrap.unbind(['up', 'k'])
    Mousetrap.unbind(['down', 'j'])
  };

  componentDidMount = () => {
    Mousetrap.bind(['left', 'h'], this.prev)
    Mousetrap.bind(['right', 'l'], this.next)
    Mousetrap.bind(['up', 'k'], (event) => {
      event.preventDefault()
      this.nextUnchecked()
    })
    Mousetrap.bind(['down', 'j'], (event) => {
      event.preventDefault()
      this.prevUnchecked()
    })
  }

  static getDerivedStateFromProps = (newProps, prevState) => {
    if (newProps.exam.id !== prevState.examID && newProps.exam.submissions.length) {
      return {
        input: newProps.exam.submissions[0].id,
        index: 0,
        examID: newProps.exam.id
      }
    }
    return null
  }

  prev = () => {
    const newIndex = this.state.index - 1

    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState((prevState, prevProps) => ({
        index: newIndex,
        input: prevProps.exam.submissions[newIndex].id
      }))
      this.props.updateSubmission(newIndex)
    }
  }
  next = () => {
    const newIndex = this.state.index + 1

    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState((prevState, prevProps) => ({
        index: newIndex,
        input: prevProps.exam.submissions[newIndex].id
      }))
      this.props.updateSubmission(newIndex)
    }
  }

  prevUnchecked = () => {
    for (let i = this.state.index - 1; i >= 0; i--) {
      if (this.props.exam.submissions[i].validated === false) {
        this.setState((prevState, prevProps) => ({
          input: prevProps.exam.submissions[i].id,
          index: i
        }))
        this.props.updateSubmission(i)
        return
      }
    }
  }
  nextUnchecked = () => {
    for (let i = this.state.index + 1; i < this.props.exam.submissions.length; i++) {
      if (this.props.exam.submissions[i].validated === false) {
        this.setState((prevState, prevProps) => ({
          input: prevProps.exam.submissions[i].id,
          index: i
        }))
        this.props.updateSubmission(i)
        return
      }
    }
  }

  setSubmission = () => {
    const input = parseInt(this.state.input)
    const i = this.props.exam.submissions.findIndex(sub => sub.id === input)

    if (i >= 0) {
      this.setState({
        index: i
      })
      this.props.updateSubmission(i)
    } else {
      this.setState((prevState, prevProps) => ({
        input: prevProps.submissions[this.state.index].id
      }))
      alert('Could not find that submission number :(\nSorry!')
    }
  }

  setSubInput = (event) => {
    const patt = new RegExp(/^([1-9]\d*|0)?$/)

    if (patt.test(event.target.value)) {
      this.setState({
        input: event.target.value
      })
    }
  }

  matchStudent = (stud) => {
    if (!this.props.exam.submissions.length) return

    api.put('submissions/' + this.props.exam.id + '/' + this.props.exam.submissions[this.state.index].id, { studentID: stud.id })
      .then(sub => {
        this.props.updateSubmission(this.state.index, sub)
        this.nextUnchecked()
      })
      .catch(err => {
        alert('failed to put submission (see javascript console for details)')
        console.error('failed to put submission:', err)
        throw err
      })
  }

  toggleEdit = (student) => {
    if (student && student.id) {
      this.setState({
        editActive: true,
        editStud: student
      })
    } else {
      this.setState(prevState => ({
        editActive: !prevState.editActive,
        editStud: null
      }))
    }
  }

  render () {
    const inputStyle = {
      width: '5em'
    }

    const subm = this.props.exam.submissions[this.state.index]

    return (
      <div>

        <Hero title='Match Students' subtitle='Check that all submissions are correctly identified' />

        <section className='section'>

          <div className='container'>

            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                {this.state.editActive
                  ? <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                  : <SearchPanel matchStudent={this.matchStudent} toggleEdit={this.toggleEdit}
                    student={subm && subm.student} validated={subm && subm.validated} subIndex={this.state.index} />
                }
              </div>

              {this.props.exam.submissions.length
                ? <div className='column'>
                  <div className='level'>
                    <div className='level-item'>
                      <div className='field has-addons is-mobile'>
                        <div className='control'>
                          <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.prevUnchecked}>unchecked</button>
                          <button type='submit' className={'button' + (subm.validated ? ' is-success' : ' is-link')}
                            onClick={this.prev}>Previous</button>
                        </div>
                        <div className='control'>
                          <input className={'input is-rounded has-text-centered' + (subm.validated ? ' is-success' : ' is-link')}
                            value={this.state.input} type='text'
                            onChange={this.setSubInput} onSubmit={this.setSubmission}
                            onBlur={this.setSubmission} maxLength='4' size='6' style={inputStyle} />
                        </div>
                        <div className='control'>
                          <button type='submit' className={'button' + (subm.validated ? ' is-success' : ' is-link')}
                            onClick={this.next}>Next</button>
                          <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.nextUnchecked}>unchecked</button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <ProgressBar progress={this.props.exam.submissions} value={'validated'} />

                  <p className='box'>
                    <img src={'api/images/signature/' + this.props.exam.id + '/' + subm.id} alt='' />
                  </p>

                </div>
                : null}
            </div>
          </div>
        </section>

      </div>
    )
  }
}

export default CheckStudents

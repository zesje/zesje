import React from 'react'
import Mousetrap from 'mousetrap'

import Notification from 'react-bulma-notification'

import * as api from '../api.jsx'

import Hero from '../components/Hero.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import SearchBox from '../components/SearchBox.jsx'

import SearchPanel from './students/SearchPanel.jsx'
import EditPanel from './students/EditPanel.jsx'

import '../components/SubmissionNavigation.css'

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

  // If we add shortcuts here, don't forget to add them
  // to ./client/components/help/ShortcutsHelp.md

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
      this.setState({
        index: newIndex,
        input: this.props.exam.submissions[newIndex].id
      })
      this.props.updateSubmission(this.props.exam.submissions[newIndex].id)
    }
  }
  next = () => {
    const newIndex = this.state.index + 1

    if (newIndex >= 0 && newIndex < this.props.exam.submissions.length) {
      this.setState({
        index: newIndex,
        input: this.props.exam.submissions[newIndex].id
      })
      this.props.updateSubmission(this.props.exam.submissions[newIndex].id)
    }
  }

  prevUnchecked = () => {
    for (let i = this.state.index - 1; i >= 0; i--) {
      if (this.props.exam.submissions[i].validated === false) {
        this.setState({
          input: this.props.exam.submissions[i].id,
          index: i
        })
        this.props.updateSubmission(this.props.exam.submissions[i].id)
        return
      }
    }
  }
  nextUnchecked = () => {
    for (let i = this.state.index + 1; i < this.props.exam.submissions.length; i++) {
      if (this.props.exam.submissions[i].validated === false) {
        this.setState({
          input: this.props.exam.submissions[i].id,
          index: i
        })
        this.props.updateSubmission(this.props.exam.submissions[i].id)
        return
      }
    }
  }

  setSubmission = (id) => {
    const i = this.props.exam.submissions.findIndex(sub => sub.id === id)
    this.setState({
      index: i
    })
    this.props.updateSubmission(id)
  }

  setSubInput = (event) => {
    const patt = new RegExp(/^([1-9]\d*|0)?$/)

    if (patt.test(event.target.value)) {
      this.setState({ input: event.target.value })
    }
  }

  matchStudent = (stud) => {
    if (!this.props.exam.submissions.length) return

    api.put('submissions/' + this.props.exam.id + '/' + this.props.exam.submissions[this.state.index].id, { studentID: stud.id })
      .then(resp => {
        this.props.updateSubmission(this.props.exam.submissions[this.state.index].id)
        this.nextUnchecked()
      })
      .catch(err => {
        Notification.error('failed to put submission (see javascript console for details)')
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
      this.setState({
        editActive: !this.state.editActive,
        editStud: null
      })
      this.props.updateSubmission(this.props.exam.submissions[this.state.index].id)
    }
  }

  render () {
    const exam = this.props.exam
    const subm = exam.submissions[this.state.index]
    const total = exam.submissions.length
    const done = exam.submissions.filter(s => s.student).length

    return (
      <div>

        <Hero title='Match Students' subtitle='Check that all submissions are correctly identified' />

        <section className='section'>

          <div className='container'>

            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                {this.state.editActive
                  ? <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                  : <SearchPanel matchStudent={this.matchStudent} toggleEdit={this.toggleEdit} submission={subm}
                    student={subm && subm.student} validated={subm && subm.validated} subIndex={this.state.index} />
                }
              </div>

              {this.props.exam.submissions.length
                ? <div className='column'>
                  <div className='level'>
                    <div className='level-item make-wider'>
                      <div className='field has-addons is-mobile'>
                        <div className='control'>
                          <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.prevUnchecked}>unchecked</button>
                          <button type='submit' className={'button' + (subm.validated ? ' is-success' : ' is-link')}
                            onClick={this.prev}>Previous</button>
                        </div>
                        <div className='control is-wider'>
                          <SearchBox
                            placeholder='Search for a submission'
                            selected={subm}
                            options={exam.submissions}
                            suggestionKeys={[
                              'id',
                              'student.firstName',
                              'student.lastName',
                              'student.id'
                            ]}
                            setSelected={this.setSubmission}
                            renderSelected={({id, student}) => {
                              if (student) {
                                return `#${id}: ${student.firstName} ${student.lastName} (${student.id})`
                              } else {
                                return `#${id}`
                              }
                            }}
                            renderSuggestion={(submission) => {
                              const stud = submission.student
                              if (stud) {
                                return (
                                  <div className='flex-parent'>
                                    <span className='flex-child truncated'>
                                      <b>#{submission.id}</b>
                                      {` ${stud.firstName} ${stud.lastName}`}
                                    </span>
                                    <i className='flex-child fixed'>
                                      ({stud.id})
                                    </i>
                                  </div>
                                )
                              } else {
                                return `#${submission.id}: No student`
                              }
                            }}
                          />
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

                  <ProgressBar done={done} total={total} />

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
